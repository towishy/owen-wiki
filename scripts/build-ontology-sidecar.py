"""Build a machine-readable ontology sidecar from markdown ontology files."""
import hashlib
import json
import re
from datetime import date
from pathlib import Path

from wiki_utils import parse_frontmatter

ROOT = Path(__file__).parent.parent
ONTOLOGY_ROOT = ROOT / 'wiki' / 'ontology'
WIKI_ROOT = ROOT / 'wiki'
OUT_JSONL = ROOT / 'outputs' / 'wiki-ops' / 'ontology-sidecar.jsonl'
OUT_MD = ROOT / 'outputs' / 'wiki-ops' / 'ontology-sidecar.md'

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
    'references': 0.65,
    'related-to': 0.50,
}


def page_index():
    index = {}
    for path in WIKI_ROOT.rglob('*.md'):
        if path.name in ('_index.md', 'README.md'):
            continue
        slug = path.stem
        category = path.relative_to(WIKI_ROOT).parts[0]
        try:
            text = path.read_text(encoding='utf-8', errors='replace')
        except Exception:
            text = ''
        meta, _body = parse_frontmatter(text)
        confidence = coerce_float(meta.get('confidence'))
        index[slug] = {
            'path': path.relative_to(ROOT).as_posix(),
            'category': category,
            'confidence': confidence,
            'title': meta.get('title', slug),
            'tags': meta.get('tags', []),
            'sources': meta.get('sources', []),
            'created': meta.get('created'),
            'updated': meta.get('updated'),
            'last_confirmed': meta.get('last_confirmed'),
            'stale_after': meta.get('stale_after'),
            'supersedes': meta.get('supersedes'),
            'superseded_by': meta.get('superseded_by'),
            'status': page_status(meta),
        }
    return index


def coerce_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def page_status(meta):
    tags = set(meta.get('tags', []))
    if meta.get('superseded_by'):
        return 'superseded'
    if 'stale' in tags:
        return 'stale'
    if 'aging' in tags:
        return 'aging'
    return 'current'


def relation_status(source_meta, target_meta):
    statuses = {source_meta.get('status'), target_meta.get('status')}
    for status in ('superseded', 'stale', 'aging'):
        if status in statuses:
            return status
    if 'current' in statuses:
        return 'current'
    return 'unknown'


def first_temporal_value(*values):
    for value in values:
        if value:
            return value
    return None


def stable_relation_id(*parts):
    raw = '|'.join(str(part) for part in parts)
    return 'rel:' + hashlib.sha1(raw.encode('utf-8')).hexdigest()[:16]


def combined_raw_sources(*page_meta):
    sources = set()
    for meta in page_meta:
        for source in meta.get('sources', []) or []:
            if 'raw/' in source:
                sources.add('raw/' + source.split('raw/', 1)[1])
    return sorted(sources)


def relation_weight(relation, source_meta, target_meta):
    base = RELATION_WEIGHTS.get(relation, 0.60)
    confidence_values = [v for v in (source_meta.get('confidence'), target_meta.get('confidence')) if isinstance(v, float)]
    if confidence_values:
        base = (base + sum(confidence_values) / len(confidence_values)) / 2
    return round(base, 3)


def evidence_tier(source_meta, target_meta):
    confidence_values = [v for v in (source_meta.get('confidence'), target_meta.get('confidence')) if isinstance(v, float)]
    if not confidence_values:
        return 'unknown'
    average = sum(confidence_values) / len(confidence_values)
    if average >= 0.85:
        return 'high'
    if average >= 0.70:
        return 'medium'
    if average >= 0.55:
        return 'low'
    return 'draft'


def main():
    pages = page_index()
    records = []
    for path in sorted(ONTOLOGY_ROOT.glob('*.md')):
        text = path.read_text(encoding='utf-8', errors='replace')
        for line_no, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if not stripped.startswith('[['):
                continue
            match = REL_RE.search(stripped)
            if not match:
                continue
            source, relation, target = match.groups()
            source_slug = source.split('|', 1)[0].split('#', 1)[0]
            target_slug = target.split('|', 1)[0].split('#', 1)[0]
            source_meta = pages.get(source_slug, {})
            target_meta = pages.get(target_slug, {})
            strength = RELATION_WEIGHTS.get(relation, 0.60)
            confidence = relation_weight(relation, source_meta, target_meta)
            relation_id = stable_relation_id(path.relative_to(ROOT).as_posix(), line_no, source_slug, relation, target_slug)
            valid_at = first_temporal_value(
                source_meta.get('last_confirmed'),
                source_meta.get('updated'),
                source_meta.get('created'),
                target_meta.get('last_confirmed'),
                target_meta.get('updated'),
                target_meta.get('created'),
            )
            invalid_at = None
            if source_meta.get('superseded_by') or target_meta.get('superseded_by'):
                invalid_at = first_temporal_value(
                    source_meta.get('updated'),
                    target_meta.get('updated'),
                    source_meta.get('stale_after'),
                    target_meta.get('stale_after'),
                )
            raw_sources = combined_raw_sources(source_meta, target_meta)
            records.append({
                'relation_id': relation_id,
                'episode_id': 'ontology:' + relation_id.removeprefix('rel:'),
                'source': source_slug,
                'relation': relation,
                'target': target_slug,
                'weight': confidence,
                'relation_strength': strength,
                'relation_confidence': confidence,
                'evidence_tier': evidence_tier(source_meta, target_meta),
                'fact_status': relation_status(source_meta, target_meta),
                'valid_at': valid_at,
                'invalid_at': invalid_at,
                'stale_after': first_temporal_value(source_meta.get('stale_after'), target_meta.get('stale_after')),
                'raw_sources': raw_sources,
                'raw_source_count': len(raw_sources),
                'source_confidence': source_meta.get('confidence'),
                'target_confidence': target_meta.get('confidence'),
                'source_category': source_meta.get('category'),
                'target_category': target_meta.get('category'),
                'source_path': source_meta.get('path'),
                'target_path': target_meta.get('path'),
                'ontology_file': path.relative_to(ROOT).as_posix(),
                'ontology_line': line_no,
                'evidence': stripped,
            })

    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text('\n'.join(json.dumps(record, ensure_ascii=False) for record in records) + '\n', encoding='utf-8')

    by_relation = {}
    by_tier = {}
    by_status = {}
    provenance_count = 0
    for record in records:
        by_relation[record['relation']] = by_relation.get(record['relation'], 0) + 1
        by_tier[record['evidence_tier']] = by_tier.get(record['evidence_tier'], 0) + 1
        by_status[record['fact_status']] = by_status.get(record['fact_status'], 0) + 1
        if record['raw_source_count']:
            provenance_count += 1
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
    lines += ['', '## Evidence Tiers', '', '| Tier | Count |', '|---|---:|']
    for tier, count in sorted(by_tier.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f'| `{tier}` | {count} |')
    lines += ['', '## Temporal / Provenance Coverage', '', '| Signal | Count |', '|---|---:|']
    lines.append(f'| Relations with raw provenance | {provenance_count} |')
    lines.append(f'| Relations with `valid_at` | {sum(1 for record in records if record.get("valid_at"))} |')
    lines.append(f'| Relations with `invalid_at` | {sum(1 for record in records if record.get("invalid_at"))} |')
    lines += ['', '## Fact Status', '', '| Status | Count |', '|---|---:|']
    for status, count in sorted(by_status.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f'| `{status}` | {count} |')
    lines += ['', '## Top Weighted Relations', '', '| Source | Relation | Target | Weight |', '|---|---|---|---:|']
    for record in sorted(records, key=lambda item: -item['weight'])[:30]:
        lines.append(f"| [[{record['source']}]] | `{record['relation']}` | [[{record['target']}]] | {record['weight']:.3f} |")
    OUT_MD.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'Relations: {len(records)}')
    print(f'JSONL: {OUT_JSONL}')
    print(f'Report: {OUT_MD}')


if __name__ == '__main__':
    main()
