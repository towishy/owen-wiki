"""Apply reviewed safe ontology relation suggestions.

Default mode is dry-run. Use --apply to update ontology markdown files.
"""
import argparse
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
QUALITY_JSON = ROOT / 'outputs' / 'drafts' / 'ontology-relation-quality.json'
OUT_MD = ROOT / 'outputs' / 'drafts' / 'ontology-relation-rewrite-plan.md'
SAFE_RELATIONS = {'covers', 'aggregates', 'uses', 'implemented-by', 'synthesizes'}
LINE_RE = re.compile(r'(\[\[[^\]]+\]\]\s*)\[related-to\](\s*\[\[[^\]]+\]\])')


def load_candidates():
    if not QUALITY_JSON.exists():
        raise SystemExit('Run scripts/check-ontology-relations.py first')
    payload = json.loads(QUALITY_JSON.read_text(encoding='utf-8'))
    return payload.get('top_candidates', [])


def eligible(record, suggestions):
    suggestion = record.get('suggestion')
    if suggestion not in SAFE_RELATIONS:
        return False
    if suggestions and suggestion not in suggestions:
        return False
    if record.get('source') == record.get('target'):
        return False
    return bool(record.get('ontology_file') and record.get('ontology_line'))


def build_plan(candidates, suggestions, limit):
    plan = []
    for record in candidates:
        if not eligible(record, suggestions):
            continue
        plan.append(record)
        if limit and len(plan) >= limit:
            break
    return plan


def apply_plan(plan, apply_changes):
    changed = []
    skipped = []
    by_file = {}
    for record in plan:
        by_file.setdefault(record['ontology_file'], []).append(record)

    for ontology_file, records in by_file.items():
        path = ROOT / ontology_file
        lines = path.read_text(encoding='utf-8').splitlines()
        file_changed = False
        for record in sorted(records, key=lambda item: item['ontology_line'], reverse=True):
            index = int(record['ontology_line']) - 1
            if index < 0 or index >= len(lines):
                skipped.append((record, 'line out of range'))
                continue
            line = lines[index]
            if '[related-to]' not in line or f"[[{record['source']}" not in line:
                skipped.append((record, 'line no longer matches'))
                continue
            new_line = LINE_RE.sub(rf'\1[{record["suggestion"]}]\2', line, count=1)
            if new_line == line:
                skipped.append((record, 'pattern not replaced'))
                continue
            changed.append((record, line, new_line))
            if apply_changes:
                lines[index] = new_line
                file_changed = True
        if apply_changes and file_changed:
            path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return changed, skipped


def render(plan, changed, skipped, apply_changes):
    today = date.today().isoformat()
    counts = Counter(record.get('suggestion') for record in plan)
    lines = [
        '---',
        'title: "Ontology Relation Rewrite Plan"',
        'type: report',
        f'updated: {today}',
        '---',
        '',
        f'# Ontology Relation Rewrite Plan - {today}',
        '',
        f'- Mode: `{"apply" if apply_changes else "dry-run"}`',
        f'- Planned: `{len(plan)}`',
        f'- Changed: `{len(changed)}`',
        f'- Skipped: `{len(skipped)}`',
        '',
        '## By Relation',
        '',
        '| Suggested relation | Count |',
        '|---|---:|',
    ]
    for relation, count in counts.most_common():
        lines.append(f'| `{relation}` | {count} |')
    lines += ['', '## Changes', '', '| Source | Old | Target | New | Ontology |', '|---|---|---|---|---|']
    for record, _old, _new in changed[:50]:
        lines.append(f"| [[{record.get('source')}]] | `related-to` | [[{record.get('target')}]] | `{record.get('suggestion')}` | `{record.get('ontology_file')}:{record.get('ontology_line')}` |")
    if not changed:
        lines.append('| - | - | - | - | - |')
    OUT_MD.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description='Apply safe ontology related-to rewrite suggestions.')
    parser.add_argument('--apply', action='store_true', help='Update ontology files. Default is dry-run.')
    parser.add_argument('--limit', type=int, default=50, help='Maximum number of suggestions to process')
    parser.add_argument('--suggestion', action='append', choices=sorted(SAFE_RELATIONS), help='Only apply this suggested relation. Can be repeated.')
    args = parser.parse_args()

    suggestions = set(args.suggestion or [])
    plan = build_plan(load_candidates(), suggestions, args.limit)
    changed, skipped = apply_plan(plan, args.apply)
    render(plan, changed, skipped, args.apply)
    print(f'Mode: {"apply" if args.apply else "dry-run"}')
    print(f'Planned: {len(plan)}')
    print(f'Changed: {len(changed)}')
    print(f'Skipped: {len(skipped)}')
    print(f'Report: {OUT_MD}')


if __name__ == '__main__':
    main()
