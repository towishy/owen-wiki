"""Build a machine-readable ontology sidecar from markdown ontology files."""
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
ONTOLOGY_ROOT = ROOT / 'wiki' / 'ontology'
WIKI_ROOT = ROOT / 'wiki'
OUT_JSONL = ROOT / 'outputs' / 'drafts' / 'ontology-sidecar.jsonl'
OUT_MD = ROOT / 'outputs' / 'drafts' / 'ontology-sidecar.md'

REL_RE = re.compile(r'\[\[([^\]]+)\]\]\s+\[([^\]]+)\]\s+\[\[([^\]]+)\]\]')
FM_RE = re.compile(r'^---\n(.*?)\n---', re.DOTALL)

RELATION_WEIGHTS = {
    'supersedes': 1.00,
    'superseded-by': 1.00,
    'deployed-at': 0.95,
    'uses': 0.90,
    'integrates-with': 0.85,
    'depends-on': 0.85,
    'covers': 0.80,
    'teaches': 0.80,
    'solves': 0.80,
    'competes-with': 0.75,
    'part-of': 0.75,
    'aggregates': 0.70,
    'related-to': 0.50,
}


def page_index():
    index = {}
    for path in WIKI_ROOT.rglob('*.md'):
        if path.name in ('_index.md', 'README.md'):
            continue
        slug = path.stem
        category = path.relative_to(WIKI_ROOT).parts[0]
        confidence = None
        try:
            text = path.read_text(encoding='utf-8', errors='replace')
        except Exception:
            text = ''
        match = FM_RE.match(text)
        if match:
            for line in match.group(1).splitlines():
                if line.startswith('confidence:'):
                    try:
                        confidence = float(line.split(':', 1)[1].strip())
                    except ValueError:
                        confidence = None
        index[slug] = {
            'path': path.relative_to(ROOT).as_posix(),
            'category': category,
            'confidence': confidence,
        }
    return index


def relation_weight(relation, source_meta, target_meta):
    base = RELATION_WEIGHTS.get(relation, 0.60)
    confidence_values = [v for v in (source_meta.get('confidence'), target_meta.get('confidence')) if isinstance(v, float)]
    if confidence_values:
        base = (base + sum(confidence_values) / len(confidence_values)) / 2
    return round(base, 3)


def main():
    pages = page_index()
    records = []
    for path in sorted(ONTOLOGY_ROOT.glob('*.md')):
        text = path.read_text(encoding='utf-8', errors='replace')
        for line_no, line in enumerate(text.splitlines(), 1):
            match = REL_RE.search(line)
            if not match:
                continue
            source, relation, target = match.groups()
            source_slug = source.split('|', 1)[0].split('#', 1)[0]
            target_slug = target.split('|', 1)[0].split('#', 1)[0]
            source_meta = pages.get(source_slug, {})
            target_meta = pages.get(target_slug, {})
            records.append({
                'source': source_slug,
                'relation': relation,
                'target': target_slug,
                'weight': relation_weight(relation, source_meta, target_meta),
                'source_category': source_meta.get('category'),
                'target_category': target_meta.get('category'),
                'source_path': source_meta.get('path'),
                'target_path': target_meta.get('path'),
                'ontology_file': path.relative_to(ROOT).as_posix(),
                'ontology_line': line_no,
                'evidence': line.strip(),
            })

    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text('\n'.join(json.dumps(record, ensure_ascii=False) for record in records) + '\n', encoding='utf-8')

    by_relation = {}
    for record in records:
        by_relation[record['relation']] = by_relation.get(record['relation'], 0) + 1
    today = date.today().isoformat()
    lines = [
        '---', 'title: "Ontology Sidecar Report"', 'type: report', f'updated: {today}', f'count: {len(records)}', '---', '',
        f'# Ontology Sidecar Report — {len(records)} relations', '',
        f'- JSONL: `{OUT_JSONL.relative_to(ROOT).as_posix()}`',
        '- 목적: Markdown ontology는 사람이 읽는 레이어로 유지하고, JSONL sidecar는 랭킹·검증·검색 가중치 계산에 사용한다.', '',
        '## Relation Counts', '', '| Relation | Count |', '|---|---:|',
    ]
    for relation, count in sorted(by_relation.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f'| `{relation}` | {count} |')
    lines += ['', '## Top Weighted Relations', '', '| Source | Relation | Target | Weight |', '|---|---|---|---:|']
    for record in sorted(records, key=lambda item: -item['weight'])[:30]:
        lines.append(f"| [[{record['source']}]] | `{record['relation']}` | [[{record['target']}]] | {record['weight']:.3f} |")
    OUT_MD.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'Relations: {len(records)}')
    print(f'JSONL: {OUT_JSONL}')
    print(f'Report: {OUT_MD}')


if __name__ == '__main__':
    main()
