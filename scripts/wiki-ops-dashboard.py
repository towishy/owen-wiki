"""Generate a single operations dashboard for the wiki."""
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCRIPTS = ROOT / 'scripts'
OUTPUTS_ROOT = ROOT / 'outputs'
OUT_MD = OUTPUTS_ROOT / 'drafts' / 'wiki-ops-dashboard.md'
OUT_JSON = OUTPUTS_ROOT / 'drafts' / 'wiki-ops-dashboard.json'
ACTION_QUEUE_JSON = OUTPUTS_ROOT / 'drafts' / 'wiki-action-queue.json'
LIFECYCLE_JSON = OUTPUTS_ROOT / 'drafts' / 'registry-promotion-lifecycle.json'
ONTOLOGY_JSONL = OUTPUTS_ROOT / 'drafts' / 'ontology-sidecar.jsonl'


def run_script(name):
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / name)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        timeout=180,
    )
    output = result.stdout + result.stderr
    return result.returncode, output


def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8'))


def parse_quality_gates(output):
    passed = 'All wiki quality gates passed' in output
    return {
        'passed': 'All wiki quality gates passed' in output,
        'broken': extract_int(output, r'Truly broken:\s+(\d+) occurrences', 0 if passed else None),
        'orphans': extract_int(output, r'Orphan pages \(0 inbound links\):\s+(\d+)', 0 if passed else None),
        'tag_violations': extract_int(output, r'Tag prefix compliance:\s+\d+ OK,\s+(\d+) non-compliant', 0 if passed else None),
        'stubs': extract_int(output, r'Stubs found:\s+(\d+)\s+/', 0 if passed else None),
    }


def extract_int(text, pattern, default=None):
    match = re.search(pattern, text)
    return int(match.group(1)) if match else default


def ontology_counts():
    if not ONTOLOGY_JSONL.exists():
        return {'relations': 0, 'by_relation': {}}
    by_relation = Counter()
    relations = 0
    for line in ONTOLOGY_JSONL.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        relations += 1
        by_relation[record.get('relation', 'unknown')] += 1
    return {'relations': relations, 'by_relation': dict(by_relation.most_common(10))}


def build_payload():
    run_script('build-ontology-sidecar.py')
    run_script('wiki-action-queue.py')
    run_script('registry-promotion-lifecycle.py')
    gate_code, gate_output = run_script('wiki-quality-gates.py')
    action_queue = load_json(ACTION_QUEUE_JSON, {})
    lifecycle = load_json(LIFECYCLE_JSON, {'items': [], 'status_counts': {}})
    return {
        'updated': date.today().isoformat(),
        'quality_gates': parse_quality_gates(gate_output) | {'exit_code': gate_code},
        'action_queue': {
            'registry_promotion_candidates': len(action_queue.get('registry_promotion_candidates', [])),
            'synthesis_candidates': len(action_queue.get('synthesis_candidates', [])),
            'tag_normalization_candidates': len(action_queue.get('tag_normalization_candidates', [])),
            'graph_registry_hints': len(action_queue.get('graph_registry_hints', [])),
            'top_registry': action_queue.get('registry_promotion_candidates', [])[:5],
            'top_synthesis': action_queue.get('synthesis_candidates', [])[:5],
        },
        'lifecycle': {
            'status_counts': lifecycle.get('status_counts', {}),
            'top_items': lifecycle.get('items', [])[:10],
        },
        'ontology': ontology_counts(),
    }


def render(payload):
    quality = payload['quality_gates']
    action = payload['action_queue']
    lifecycle = payload['lifecycle']
    ontology = payload['ontology']
    today = payload['updated']
    status = 'PASS' if quality.get('passed') and quality.get('exit_code') == 0 else 'CHECK'
    lines = [
        '---',
        'title: "Wiki Operations Dashboard"',
        'type: report',
        f'updated: {today}',
        '---',
        '',
        f'# Wiki Operations Dashboard — {today}',
        '',
        f'**Overall status:** `{status}`',
        '',
        '## Quality Gates',
        '',
        '| Gate | Value |',
        '|---|---:|',
        f"| Broken links | {quality.get('broken')} |",
        f"| Orphan pages | {quality.get('orphans')} |",
        f"| Tag violations | {quality.get('tag_violations')} |",
        f"| Stub pages | {quality.get('stubs')} |",
        '',
        '## Action Queue',
        '',
        '| Queue | Count |',
        '|---|---:|',
        f"| Registry promotion candidates | {action.get('registry_promotion_candidates', 0)} |",
        f"| Synthesis candidates | {action.get('synthesis_candidates', 0)} |",
        f"| Tag normalization candidates | {action.get('tag_normalization_candidates', 0)} |",
        f"| Registry ranking hints | {action.get('graph_registry_hints', 0)} |",
        '',
        '### Top Registry Promotions',
        '',
        '| Rank | Page | Score | Sources | Signals |',
        '|---:|---|---:|---:|---|',
    ]
    for rank, item in enumerate(action.get('top_registry', []), 1):
        lines.append(f"| {rank} | [[{item.get('page')}]] | {item.get('score')} | {item.get('sources')} | {item.get('signals')} |")
    if not action.get('top_registry'):
        lines.append('| - | - | - | - | - |')

    lines += [
        '',
        '### Top Synthesis Themes',
        '',
        '| Rank | Theme | Score | Summary pages |',
        '|---:|---|---:|---:|',
    ]
    for rank, item in enumerate(action.get('top_synthesis', []), 1):
        lines.append(f"| {rank} | `{item.get('theme')}` | {item.get('score')} | {item.get('summary_pages')} |")
    if not action.get('top_synthesis'):
        lines.append('| - | - | - | - |')

    lines += [
        '',
        '## Registry Promotion Lifecycle',
        '',
        '| Status | Count |',
        '|---|---:|',
    ]
    for status_name, count in lifecycle.get('status_counts', {}).items():
        lines.append(f'| `{status_name}` | {count} |')
    lines += [
        '',
        '## Ontology Sidecar',
        '',
        f"- Relations: `{ontology.get('relations', 0)}`",
        '- Sidecar: `outputs/drafts/ontology-sidecar.jsonl`',
        '',
        '| Relation | Count |',
        '|---|---:|',
    ]
    for relation, count in ontology.get('by_relation', {}).items():
        lines.append(f'| `{relation}` | {count} |')
    lines += [
        '',
        '## Next Operating Moves',
        '',
        '1. Review `outputs/drafts/registry-promotion-lifecycle.md` and mark Top 5 candidates as `sampled` or `deferred`.',
        '2. Promote one high-value registry candidate to curated summary before adding more source registry pages.',
        '3. Use curated summary/entity/concept/synthesis first in query answers; use registry pages as coverage evidence only.',
        '',
    ]
    return '\n'.join(lines)


def main():
    payload = build_payload()
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    OUT_MD.write_text(render(payload), encoding='utf-8')
    print(f'Dashboard: {OUT_MD}')
    print(f'JSON: {OUT_JSON}')


if __name__ == '__main__':
    main()