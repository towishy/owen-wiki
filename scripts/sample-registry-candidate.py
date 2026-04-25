"""Create a representative sampling packet for a source registry candidate."""
import argparse
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
WIKI_ROOT = ROOT / 'wiki'
ACTION_QUEUE_JSON = ROOT / 'outputs' / 'drafts' / 'wiki-action-queue.json'
LIFECYCLE_JSON = ROOT / 'outputs' / 'drafts' / 'registry-promotion-lifecycle.json'
OUT_DIR = ROOT / 'outputs' / 'drafts' / 'registry-samples'

FM_RE = re.compile(r'^---\n(.*?)\n---', re.DOTALL)
PRODUCT_HINTS = ('sentinel', 'entra', 'intune', 'mde', 'defender', 'purview', 'copilot', 'xdr', 'mdc')
CUSTOMER_HINTS = ('hyundai', '현대', 'krafton', '크래프톤', 'kt', 'kb', 'sk', 'lg', 'naver', '네이버')
LOW_VALUE_HINTS = ('_templates', '_moc', 'template', 'attachment', 'archive')


def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8'))


def parse_sources(content):
    match = FM_RE.match(content)
    if not match:
        return []
    sources = []
    current_key = None
    for line in match.group(1).splitlines():
        if line.startswith('sources:'):
            current_key = 'sources'
            value = line.split(':', 1)[1].strip()
            if value.startswith('[') and value.endswith(']'):
                inner = value[1:-1].strip()
                sources.extend(item.strip().strip('"').strip("'") for item in inner.split(',') if item.strip())
            elif value:
                sources.append(value.strip('"').strip("'"))
            continue
        if current_key == 'sources' and line.startswith('  - '):
            sources.append(line[4:].strip().strip('"').strip("'"))
        elif line and not line.startswith(' '):
            current_key = None
    return sources


def find_page(page_slug):
    for path in WIKI_ROOT.rglob(f'{page_slug}.md'):
        return path
    raise SystemExit(f'Page not found: {page_slug}')


def source_score(source):
    haystack = source.lower()
    score = 0
    score += sum(3 for hint in PRODUCT_HINTS if hint in haystack)
    score += sum(4 for hint in CUSTOMER_HINTS if hint in haystack)
    score -= sum(4 for hint in LOW_VALUE_HINTS if hint in haystack)
    if 'extracted/' in haystack:
        score += 2
    if any(token in haystack for token in ('workshop', 'assessment', 'readiness', 'pilot', 'mvp')):
        score += 2
    if haystack.endswith(('.md', '.pdf', '.pptx', '.docx', '.xlsx')):
        score += 1
    return score


def source_group(source):
    parts = source.split('/')
    return '/'.join(parts[:3]) if len(parts) >= 3 else source


def read_snippet(source):
    path = ROOT / source
    if not path.exists() or path.suffix.lower() != '.md':
        return ''
    try:
        lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
    except Exception:
        return ''
    useful = [line.strip() for line in lines if line.strip() and not line.startswith('---')]
    return ' '.join(useful[:3])[:500]


def select_samples(sources, limit):
    ranked = sorted(sources, key=lambda source: (-source_score(source), source))
    selected = []
    seen_groups = set()
    for source in ranked:
        group = source_group(source)
        if group in seen_groups and len(selected) < min(limit, 3):
            continue
        selected.append(source)
        seen_groups.add(group)
        if len(selected) >= limit:
            break
    for source in ranked:
        if len(selected) >= limit:
            break
        if source not in selected:
            selected.append(source)
    return selected


def candidate_record(page_slug):
    queue = load_json(ACTION_QUEUE_JSON, {})
    lifecycle = load_json(LIFECYCLE_JSON, {})
    records = {item.get('page'): item for item in queue.get('registry_promotion_candidates', [])}
    records.update({item.get('page'): item for item in lifecycle.get('items', [])})
    return records.get(page_slug, {})


def recommendation(record, sources):
    signals = record.get('signals', '').lower()
    haystack = ' '.join(sources).lower()
    if 'generic-outputs' in signals or 'generic-_templates' in signals or 'generic-_moc' in signals:
        return 'defer', 'generic registry 성격이 강하므로 curated summary보다 coverage 증명으로 유지 권장'
    if any(hint in haystack for hint in CUSTOMER_HINTS):
        return 'sample', '고객/프로젝트 신호가 있어 대표 원본 검토 가치가 높음'
    if any(hint in haystack for hint in PRODUCT_HINTS):
        return 'sample', '제품 중심 raw 묶음으로 summary 승격 가능성 있음'
    return 'review', '자동 신호가 약해 사람 검토 필요'


def render(page_slug, record, sources, samples):
    today = date.today().isoformat()
    action, reason = recommendation(record, sources)
    groups = Counter(source_group(source) for source in sources)
    lines = [
        '---',
        f'title: "Registry Sample - {page_slug}"',
        'type: report',
        f'updated: {today}',
        '---',
        '',
        f'# Registry Sample - {page_slug}',
        '',
        f'- Candidate page: [[{page_slug}]]',
        f'- Sources: `{len(sources)}`',
        f'- Queue score: `{record.get("score", "-")}`',
        f'- Signals: `{record.get("signals", "-")}`',
        f'- Recommended action: `{action}` - {reason}',
        '',
        '## Source Groups',
        '',
        '| Group | Count |',
        '|---|---:|',
    ]
    for group, count in groups.most_common(10):
        lines.append(f'| `{group}` | {count} |')
    lines += ['', '## Representative Samples', '', '| Rank | Score | Source | Snippet |', '|---:|---:|---|---|']
    for index, source in enumerate(samples, 1):
        snippet = read_snippet(source).replace('|', '\\|') or '-'
        lines.append(f'| {index} | {source_score(source)} | `{source}` | {snippet} |')
    lines += ['', '## Next Decision', '', '- `sampled`: 대표 원본을 읽고 별도 curated summary 가치가 있으면 승격한다.', '- `deferred`: 중복/저가치/generic 묶음이면 registry coverage로만 유지한다.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Create a representative sample report for a registry candidate.')
    parser.add_argument('page', nargs='?', help='Registry candidate page slug. Defaults to top action queue candidate.')
    parser.add_argument('--limit', type=int, default=5, help='Number of representative sources to include')
    args = parser.parse_args()

    queue = load_json(ACTION_QUEUE_JSON, {'registry_promotion_candidates': []})
    page_slug = args.page or (queue.get('registry_promotion_candidates') or [{}])[0].get('page')
    if not page_slug:
        raise SystemExit('No registry candidate found')
    page_path = find_page(page_slug)
    sources = parse_sources(page_path.read_text(encoding='utf-8', errors='replace'))
    samples = select_samples(sources, args.limit)
    record = candidate_record(page_slug)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        'updated': date.today().isoformat(),
        'page': page_slug,
        'path': page_path.relative_to(ROOT).as_posix(),
        'source_count': len(sources),
        'samples': [{'source': source, 'score': source_score(source), 'snippet': read_snippet(source)} for source in samples],
        'record': record,
    }
    out_json = OUT_DIR / f'{page_slug}.json'
    out_md = OUT_DIR / f'{page_slug}.md'
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    out_md.write_text(render(page_slug, record, sources, samples), encoding='utf-8')
    print(f'Sample report: {out_md}')
    print(f'Sample JSON: {out_json}')


if __name__ == '__main__':
    main()
