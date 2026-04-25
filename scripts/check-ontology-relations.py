"""Report weak ontology relations that should be made more specific."""
import json
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
SIDE_CAR = ROOT / 'outputs' / 'drafts' / 'ontology-sidecar.jsonl'
OUT_MD = ROOT / 'outputs' / 'drafts' / 'ontology-relation-quality.md'
OUT_JSON = ROOT / 'outputs' / 'drafts' / 'ontology-relation-quality.json'

WEAK_RELATIONS = {'related-to'}
SUGGESTIONS = {
    ('summaries', 'entities'): 'covers',
    ('summaries', 'concepts'): 'covers',
    ('synthesis', 'summaries'): 'aggregates',
    ('synthesis', 'concepts'): 'synthesizes',
    ('entities', 'concepts'): 'uses',
    ('concepts', 'entities'): 'implemented-by',
}


def load_records():
    if not SIDE_CAR.exists():
        return []
    records = []
    for line in SIDE_CAR.read_text(encoding='utf-8').splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def suggest(record):
    key = (record.get('source_category'), record.get('target_category'))
    return SUGGESTIONS.get(key, 'more-specific-relation')


def main():
    records = load_records()
    weak = [record | {'suggestion': suggest(record)} for record in records if record.get('relation') in WEAK_RELATIONS]
    by_suggestion = Counter(record['suggestion'] for record in weak)
    payload = {
        'updated': date.today().isoformat(),
        'relations': len(records),
        'weak_related_to_count': len(weak),
        'suggestions': dict(by_suggestion),
        'top_candidates': weak[:50],
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    lines = [
        '---',
        'title: "Ontology Relation Quality"',
        'type: report',
        f'updated: {payload["updated"]}',
        '---',
        '',
        f'# Ontology Relation Quality — {payload["updated"]}',
        '',
        f'- Total relations: `{len(records)}`',
        f'- Weak `related-to` candidates: `{len(weak)}`',
        '',
        '## Suggested Rewrites',
        '',
        '| Suggestion | Count |',
        '|---|---:|',
    ]
    for relation, count in by_suggestion.most_common():
        lines.append(f'| `{relation}` | {count} |')
    lines += ['', '## Top Candidates', '', '| Source | Current | Target | Suggestion | Ontology |', '|---|---|---|---|---|']
    for record in weak[:30]:
        lines.append(
            f"| [[{record.get('source')}]] | `{record.get('relation')}` | [[{record.get('target')}]] | `{record.get('suggestion')}` | `{record.get('ontology_file')}:{record.get('ontology_line')}` |"
        )
    OUT_MD.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'Relations: {len(records)}')
    print(f'Weak related-to: {len(weak)}')
    print(f'Report: {OUT_MD}')


if __name__ == '__main__':
    main()