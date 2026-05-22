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
OUT_MD = OUTPUTS_ROOT / 'wiki-ops' / 'wiki-ops-dashboard.md'
OUT_JSON = OUTPUTS_ROOT / 'wiki-ops' / 'wiki-ops-dashboard.json'
ACTION_QUEUE_JSON = OUTPUTS_ROOT / 'wiki-ops' / 'wiki-action-queue.json'
LIFECYCLE_JSON = OUTPUTS_ROOT / 'wiki-ops' / 'registry-promotion-lifecycle.json'
ONTOLOGY_JSONL = OUTPUTS_ROOT / 'wiki-ops' / 'ontology-sidecar.jsonl'
EPISODE_LEDGER_JSONL = OUTPUTS_ROOT / 'wiki-ops' / 'episode-ledger.jsonl'
RELATION_QUALITY_JSON = OUTPUTS_ROOT / 'wiki-ops' / 'ontology-relation-quality.json'
REPO_METRICS_JSON = OUTPUTS_ROOT / 'wiki-ops' / 'repo-metrics.json'
GRAPH_HYGIENE_JSON = OUTPUTS_ROOT / 'wiki-ops' / 'graph-hygiene.json'
GRAPH_DELTA_JSON = OUTPUTS_ROOT / 'wiki-ops' / 'graph-delta.json'
REGISTRY_WORKBENCH_JSON = OUTPUTS_ROOT / 'wiki-ops' / 'registry-promotion-workbench.json'


def run_script(name, *args):
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args],
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


def episode_counts():
    if not EPISODE_LEDGER_JSONL.exists():
        return {'episodes': 0, 'existing': 0, 'missing': 0, 'with_relations': 0, 'top_groups': {}}
    episodes = 0
    existing = 0
    with_relations = 0
    groups = Counter()
    for line in EPISODE_LEDGER_JSONL.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        episodes += 1
        if record.get('source_exists'):
            existing += 1
        if record.get('derived_relation_count'):
            with_relations += 1
        groups[record.get('source_group', 'unknown')] += 1
    return {
        'episodes': episodes,
        'existing': existing,
        'missing': episodes - existing,
        'with_relations': with_relations,
        'top_groups': dict(groups.most_common(5)),
    }


def build_payload():
    previous = load_json(OUT_JSON, {})
    run_script('wiki-stats.py', '--write-ops')
    run_script('build-ontology-sidecar.py')
    run_script('build-episode-ledger.py')
    run_script('wiki-action-queue.py')
    run_script('registry-promotion-lifecycle.py')
    run_script('check-ontology-relations.py')
    run_script('check-graph-hygiene.py')
    run_script('graph-delta-report.py')
    run_script('registry-promotion-workbench.py')
    gate_code, gate_output = run_script('wiki-quality-gates.py')
    action_queue = load_json(ACTION_QUEUE_JSON, {})
    lifecycle = load_json(LIFECYCLE_JSON, {'items': [], 'status_counts': {}})
    relation_quality = load_json(RELATION_QUALITY_JSON, {})
    graph_hygiene = load_json(GRAPH_HYGIENE_JSON, {})
    graph_delta = load_json(GRAPH_DELTA_JSON, {})
    registry_workbench = load_json(REGISTRY_WORKBENCH_JSON, {})
    payload = {
        'updated': date.today().isoformat(),
        'repo_metrics': load_json(REPO_METRICS_JSON, {}),
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
        'episodes': episode_counts(),
        'relation_quality': relation_quality,
        'graph_hygiene': graph_hygiene,
        'graph_delta': graph_delta,
        'registry_workbench': {
            'packets': len(registry_workbench.get('packets', [])),
            'top_packets': registry_workbench.get('packets', [])[:5],
        },
    }
    payload['delta'] = compute_delta(previous, payload)
    return payload


def compute_delta(previous, current):
    if not previous:
        return {}
    fields = {
        'registry_promotion_candidates': ('action_queue', 'registry_promotion_candidates'),
        'synthesis_candidates': ('action_queue', 'synthesis_candidates'),
        'tag_normalization_candidates': ('action_queue', 'tag_normalization_candidates'),
        'ontology_relations': ('ontology', 'relations'),
        'weak_related_to': ('relation_quality', 'weak_related_to_count'),
    }
    delta = {}
    for name, path in fields.items():
        old = nested_get(previous, path)
        new = nested_get(current, path)
        if isinstance(old, int) and isinstance(new, int):
            delta[name] = new - old
    return delta


def nested_get(data, path):
    value = data
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def render(payload):
    repo_metrics = payload.get('repo_metrics', {})
    quality = payload['quality_gates']
    action = payload['action_queue']
    lifecycle = payload['lifecycle']
    ontology = payload['ontology']
    episodes = payload.get('episodes', {})
    relation_quality = payload.get('relation_quality', {})
    graph_hygiene = payload.get('graph_hygiene', {})
    graph_delta = payload.get('graph_delta', {})
    registry_workbench = payload.get('registry_workbench', {})
    delta = payload.get('delta', {})
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
        '## Canonical Repository Metrics',
        '',
        '- Source: `outputs/wiki-ops/repo-metrics.json`',
        '',
        '| Metric | Value |',
        '|---|---:|',
        f"| Wiki pages | {nested_get(repo_metrics, ('pages', 'total')) or 0} |",
        f"| Wikilinks | {nested_get(repo_metrics, ('content', 'wikilinks')) or 0} |",
        f"| Total lines | {nested_get(repo_metrics, ('content', 'total_lines')) or 0} |",
        f"| Total words | {nested_get(repo_metrics, ('content', 'total_words')) or 0} |",
        f"| Unique tags | {nested_get(repo_metrics, ('tags', 'unique')) or 0} |",
        f"| Raw source files | {nested_get(repo_metrics, ('raw_sources', 'files')) or 0} |",
        f"| Git commits | {nested_get(repo_metrics, ('git', 'commits')) or 0} |",
        '',
        '## Quality Gates',
        '',
        '| Gate | Value |',
        '|---|---:|',
        f"| Broken links | {quality.get('broken')} |",
        f"| Orphan pages | {quality.get('orphans')} |",
        f"| Tag violations | {quality.get('tag_violations')} |",
        f"| Stub pages | {quality.get('stubs')} |",
        f"| Graph hygiene issues | {graph_hygiene.get('issue_count', 0)} |",
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
        '## Trend Delta',
        '',
        '| Metric | Delta since previous run |',
        '|---|---:|',
        f"| Registry promotion candidates | {delta.get('registry_promotion_candidates', 0)} |",
        f"| Synthesis candidates | {delta.get('synthesis_candidates', 0)} |",
        f"| Tag normalization candidates | {delta.get('tag_normalization_candidates', 0)} |",
        f"| Ontology relations | {delta.get('ontology_relations', 0)} |",
        f"| Weak `related-to` relations | {delta.get('weak_related_to', 0)} |",
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
        '- Sidecar: `outputs/wiki-ops/ontology-sidecar.jsonl`',
        '',
        '| Relation | Count |',
        '|---|---:|',
    ]
    for relation, count in ontology.get('by_relation', {}).items():
        lines.append(f'| `{relation}` | {count} |')
    lines += [
        '',
        '## Episode Ledger',
        '',
        f"- Episodes: `{episodes.get('episodes', 0)}`",
        '- Ledger: `outputs/wiki-ops/episode-ledger.jsonl`',
        '',
        '| Signal | Count |',
        '|---|---:|',
        f"| Existing raw files | {episodes.get('existing', 0)} |",
        f"| Missing raw references | {episodes.get('missing', 0)} |",
        f"| Episodes linked to ontology relations | {episodes.get('with_relations', 0)} |",
        '',
        '| Top source group | Episodes |',
        '|---|---:|',
    ]
    for group, count in episodes.get('top_groups', {}).items():
        lines.append(f'| `{group}` | {count} |')
    lines += [
        '',
        '## Ontology Relation Quality',
        '',
        f"- Weak `related-to` candidates: `{relation_quality.get('weak_related_to_count', 0)}`",
        f"- Report: `outputs/wiki-ops/ontology-relation-quality.md`",
        '',
        '## Graph Hygiene & Delta',
        '',
        f"- Hygiene issues: `{graph_hygiene.get('issue_count', 0)}`",
        f"- Escaped aliases normalized: `{graph_hygiene.get('escaped_aliases', 0)}`",
        f"- Graph delta: nodes `{nested_get(graph_delta, ('delta', 'nodes')) or 0:+d}`, edges `{nested_get(graph_delta, ('delta', 'edges')) or 0:+d}`",
        '',
        '## Registry Promotion Workbench',
        '',
        f"- Review packets: `{registry_workbench.get('packets', 0)}`",
        f"- Report: `outputs/wiki-ops/registry-promotion-workbench.md`",
        '',
        '',
        '## Next Operating Moves',
        '',
        '1. Review `outputs/wiki-ops/registry-promotion-lifecycle.md` and mark Top 5 candidates as `sampled` or `deferred`.',
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