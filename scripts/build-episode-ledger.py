"""Build a Graphiti-inspired episode ledger for raw source provenance.

The ledger records each referenced raw source as an immutable episode and links
it to derived wiki pages and ontology relations. It complements
raw-to-wiki-map.json by keeping stable episode IDs, file fingerprints, and
relation lineage in JSONL form.
"""
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

from wiki_utils import OUTPUTS_ROOT, ROOT, iter_wiki_pages

OUT_JSONL = OUTPUTS_ROOT / 'wiki-ops' / 'episode-ledger.jsonl'
OUT_MD = OUTPUTS_ROOT / 'wiki-ops' / 'episode-ledger.md'
ONTOLOGY_JSONL = OUTPUTS_ROOT / 'wiki-ops' / 'ontology-sidecar.jsonl'

RAW_REF_RE = re.compile(r'(raw/[\w\-./ \u00a0가-힣()\[\]&,+]+?\.(?:md|pdf|pptx|docx|xlsx|csv|json|svg|png|jpg|jpeg))', re.IGNORECASE)
RAW_FILE_RE = re.compile(r'(raw/.+?\.(?:md|pdf|pptx|docx|xlsx|csv|json|svg|png|jpg|jpeg|txt))', re.IGNORECASE)


def stable_id(prefix, value):
    return f'{prefix}:' + hashlib.sha1(value.encode('utf-8')).hexdigest()[:16]


def normalize_raw_ref(value):
    if not value or 'raw/' not in value:
        return None
    raw = 'raw/' + value.split('raw/', 1)[1]
    raw = raw.split('#', 1)[0].strip().strip('"\'`')
    file_match = RAW_FILE_RE.search(raw)
    if file_match:
        raw = file_match.group(1)
    return raw.replace('\\', '/')


def source_suffix(raw_path):
    path = Path(raw_path)
    if raw_path.endswith('/') or not path.suffix:
        return '(directory)'
    return path.suffix.lower()


def source_group(raw_path):
    parts = Path(raw_path).parts
    if len(parts) >= 3:
        return '/'.join(parts[:3])
    return '/'.join(parts)


def collect_page_sources():
    raw_to_pages = defaultdict(list)
    page_meta = {}
    for page in iter_wiki_pages():
        page_meta[page['slug']] = {
            'path': page['path'],
            'title': page['title'],
            'category': page['category'],
            'tags': page['tags'],
        }
        refs = set()
        for source in page.get('sources', []) or []:
            normalized = normalize_raw_ref(source)
            if normalized:
                refs.add(normalized)
        for match in RAW_REF_RE.findall(page['content']):
            normalized = normalize_raw_ref(match)
            if normalized:
                refs.add(normalized)
        for raw_path in refs:
            raw_to_pages[raw_path].append(page['slug'])
    return raw_to_pages, page_meta


def relation_index():
    by_page = defaultdict(list)
    if not ONTOLOGY_JSONL.exists():
        return by_page
    for line in ONTOLOGY_JSONL.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        relation_id = record.get('relation_id') or stable_id(
            'rel', f"{record.get('source')}|{record.get('relation')}|{record.get('target')}"
        )
        for key in ('source', 'target'):
            page = record.get(key)
            if page:
                by_page[page].append(relation_id)
    return by_page


def file_stats(raw_path):
    path = ROOT / raw_path
    if not path.exists():
        return {
            'source_exists': False,
            'size_bytes': None,
            'modified_at': None,
            'content_fingerprint': stable_id('missing', raw_path),
        }
    stat = path.stat()
    modified_at = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
    fingerprint_source = f'{raw_path}|{stat.st_size}|{stat.st_mtime_ns}'
    return {
        'source_exists': True,
        'size_bytes': stat.st_size,
        'modified_at': modified_at,
        'content_fingerprint': stable_id('file', fingerprint_source),
    }


def build_records():
    raw_to_pages, page_meta = collect_page_sources()
    relations_by_page = relation_index()
    records = []
    for raw_path, slugs in sorted(raw_to_pages.items()):
        unique_slugs = sorted(set(slugs))
        relation_ids = sorted({relation for slug in unique_slugs for relation in relations_by_page.get(slug, [])})
        tags = Counter(tag for slug in unique_slugs for tag in page_meta.get(slug, {}).get('tags', []))
        derived_pages = [page_meta[slug]['path'] for slug in unique_slugs if slug in page_meta]
        records.append({
            'episode_id': stable_id('raw', raw_path),
            'episode_type': 'raw_source',
            'source_path': raw_path,
            'source_suffix': source_suffix(raw_path),
            'source_group': source_group(raw_path),
            **file_stats(raw_path),
            'derived_pages': derived_pages,
            'derived_page_count': len(derived_pages),
            'derived_relations': relation_ids[:50],
            'derived_relation_count': len(relation_ids),
            'top_tags': [tag for tag, _count in tags.most_common(10)],
        })
    return records


def render_report(records):
    today = date.today().isoformat()
    existing = sum(1 for record in records if record['source_exists'])
    with_relations = sum(1 for record in records if record['derived_relation_count'])
    by_group = Counter(record['source_group'] for record in records)
    by_suffix = Counter(record['source_suffix'] or '(none)' for record in records)
    lines = [
        '---',
        'title: "Episode Ledger Report"',
        'type: report',
        f'updated: {today}',
        f'count: {len(records)}',
        '---',
        '',
        f'# Episode Ledger Report — {len(records)} episodes',
        '',
        f'- JSONL: `{OUT_JSONL.relative_to(ROOT).as_posix()}`',
        '- 목적: Graphiti의 episode provenance 모델을 markdown-native WIKI에 맞게 적용해 raw 원본과 파생 wiki/ontology를 추적한다.',
        '',
        '## Coverage',
        '',
        '| Signal | Count |',
        '|---|---:|',
        f'| Existing raw files | {existing} |',
        f'| Missing raw references | {len(records) - existing} |',
        f'| Episodes linked to ontology relations | {with_relations} |',
        '',
        '## Top Source Groups',
        '',
        '| Group | Episodes |',
        '|---|---:|',
    ]
    for group, count in by_group.most_common(20):
        lines.append(f'| `{group}` | {count} |')
    lines += ['', '## Source Types', '', '| Suffix | Episodes |', '|---|---:|']
    for suffix, count in by_suffix.most_common():
        lines.append(f'| `{suffix}` | {count} |')
    lines += ['', '## Most Reused Episodes', '', '| Source | Derived pages | Relations |', '|---|---:|---:|']
    for record in sorted(records, key=lambda item: (-item['derived_page_count'], -item['derived_relation_count'], item['source_path']))[:20]:
        lines.append(
            f"| `{record['source_path']}` | {record['derived_page_count']} | {record['derived_relation_count']} |"
        )
    return '\n'.join(lines) + '\n'


def main():
    records = build_records()
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text('\n'.join(json.dumps(record, ensure_ascii=False) for record in records) + '\n', encoding='utf-8')
    OUT_MD.write_text(render_report(records), encoding='utf-8')
    print(f'Episodes: {len(records)}')
    print(f'JSONL: {OUT_JSONL}')
    print(f'Report: {OUT_MD}')


if __name__ == '__main__':
    main()
