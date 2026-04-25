"""Generate a prioritized wiki action queue.

This report turns healthy-repository signals into next actions:
- source registry pages that should be promoted to curated summaries
- synthesis themes that are large enough to deserve a synthesis page
- tag normalization candidates
- raw source knowledge grades (registered/summarized/linked/synthesized/output-used)
- graph/search ranking hints for registry hubs
"""
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
WIKI_ROOT = ROOT / 'wiki'
OUTPUTS_ROOT = ROOT / 'outputs'
OUT_MD = OUTPUTS_ROOT / 'drafts' / 'wiki-action-queue.md'
OUT_JSON = OUTPUTS_ROOT / 'drafts' / 'wiki-action-queue.json'
TAG_ALIASES = ROOT / 'scripts' / 'tag-aliases.yml'
GRAPH_JSON = ROOT / 'graphify-out' / 'graph.json'

FM_RE = re.compile(r'^---\n(.*?)\n---', re.DOTALL)
WIKILINK_RE = re.compile(r'\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]')
RAW_REF_RE = re.compile(r'raw/[^`<>\n]+')
PRODUCT_KEYWORDS = {
    'mde': 'prod/mde',
    'defender-for-endpoint': 'prod/mde',
    'sentinel': 'prod/sentinel',
    'purview': 'prod/purview',
    'dlp': 'prod/purview-dlp',
    'entra': 'prod/entra',
    'identity': 'topic/identity',
    'intune': 'prod/intune',
    'copilot': 'prod/security-copilot',
    'defender-for-cloud': 'prod/mdc',
    'mdc': 'prod/mdc',
    'xdr': 'prod/m365-defender-xdr',
}
CUSTOMER_KEYWORDS = ('hyundai', '현대', 'krafton', '크래프톤', 'naver', '네이버', 'ncsoft', '넷마블', 'kb', '농협', 'lg', 'sk')
GENERIC_REGISTRY_PENALTIES = {
    'outputs': 10,
    '_templates': 8,
    '_moc': 8,
    'misc': 4,
}


def md_cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')


def slug(path):
    return path.stem


def parse_inline_list(value):
    value = value.strip()
    if not (value.startswith('[') and value.endswith(']')):
        return []
    inner = value[1:-1].strip()
    if not inner:
        return []
    return [item.strip().strip('"').strip("'") for item in inner.split(',') if item.strip()]


def parse_frontmatter(content):
    match = FM_RE.match(content)
    if not match:
        return {}, content
    fm_text = match.group(1)
    body = content[match.end():]
    meta = {'tags': [], 'sources': []}
    current_key = None
    for line in fm_text.splitlines():
        if not line.strip():
            continue
        if line.startswith('  - ') and current_key in ('tags', 'sources'):
            meta[current_key].append(line[4:].strip().strip('"').strip("'"))
            continue
        current_key = None
        if ':' not in line:
            continue
        key, raw_value = line.split(':', 1)
        key = key.strip()
        value = raw_value.strip()
        if key in ('tags', 'sources'):
            current_key = key
            if value.startswith('['):
                meta[key].extend(parse_inline_list(value))
            elif value:
                meta[key].append(value.strip('"').strip("'"))
        else:
            meta[key] = value.strip('"').strip("'")
    return meta, body


def load_pages():
    pages = []
    for path in sorted(WIKI_ROOT.rglob('*.md')):
        if path.name in ('_index.md', 'README.md'):
            continue
        content = path.read_text(encoding='utf-8', errors='replace')
        meta, body = parse_frontmatter(content)
        rel = path.relative_to(ROOT).as_posix()
        category = path.relative_to(WIKI_ROOT).parts[0]
        tags = meta.get('tags', [])
        sources = meta.get('sources', [])
        raw_refs = set()
        for source in sources:
            if 'raw/' in source:
                raw_refs.add('raw/' + source.split('raw/', 1)[1])
        for ref in RAW_REF_RE.findall(body):
            raw_refs.add(ref.rstrip(' \t.,;:)]"\''))
        pages.append({
            'slug': slug(path),
            'path': rel,
            'category': category,
            'type': meta.get('type', ''),
            'title': meta.get('title', slug(path)),
            'tags': tags,
            'sources': sources,
            'source_count': len(sources),
            'raw_refs': raw_refs,
            'links': set(WIKILINK_RE.findall(body)),
            'body_len': len(body.strip()),
            'is_registry': 'type/source-registry' in tags or slug(path).startswith('remaining-raw-'),
        })
    return pages


def registry_promotion_candidates(pages):
    candidates_by_group = {}
    for page in pages:
        if not page['is_registry'] or page['slug'] == 'remaining-raw-source-registry-hub':
            continue
        haystack = ' '.join([page['slug'], page['title'], *page['sources']]).lower()
        product_hits = sorted({tag for key, tag in PRODUCT_KEYWORDS.items() if key in haystack})
        customer_hit = any(key in haystack for key in CUSTOMER_KEYWORDS)
        source_score = min(page['source_count'] // 10, 10)
        score = source_score + len(product_hits) * 3 + (3 if customer_hit else 0)
        penalties = []
        for token, penalty in GENERIC_REGISTRY_PENALTIES.items():
            if token in haystack:
                score -= penalty
                penalties.append(f'generic-{token} -{penalty}')
        if len(product_hits) >= 7:
            score -= 3
            penalties.append('broad-product-mix -3')
        if 'workshop' in haystack or 'assessment' in haystack or 'architecture' in haystack:
            score += 2
        if page['source_count'] >= 20 or product_hits or customer_hit:
            group = registry_group_key(page['slug'])
            candidate = {
                'page': page['slug'],
                'path': page['path'],
                'score': score,
                'sources': page['source_count'],
                'signals': ', '.join(product_hits + (['customer'] if customer_hit else []) + penalties) or 'source-volume',
                'group': group,
            }
            current = candidates_by_group.get(group)
            if not current or (candidate['score'], candidate['sources']) > (current['score'], current['sources']):
                candidates_by_group[group] = candidate
    group_sizes = Counter(registry_group_key(page['slug']) for page in pages if page['is_registry'])
    candidates = []
    for candidate in candidates_by_group.values():
        candidate['group_size'] = group_sizes.get(candidate['group'], 1)
        candidates.append(candidate)
    return sorted(candidates, key=lambda item: (-item['score'], -item['sources'], item['page']))[:30]


def registry_group_key(page_slug):
    return re.sub(r'-part-\d+-([0-9a-f]{8})$', r'-parts-\1', page_slug)


def synthesis_candidates(pages):
    existing = set()
    for page in pages:
        if page['category'] == 'synthesis':
            existing.update(tag for tag in page['tags'] if tag.startswith(('prod/', 'topic/', 'customer/')))
            existing.add(page['slug'])

    grouped = Counter()
    examples = defaultdict(list)
    for page in pages:
        if page['category'] != 'summaries' or page['is_registry']:
            continue
        tags = [tag for tag in page['tags'] if tag.startswith(('prod/', 'topic/', 'customer/'))]
        for tag in tags:
            grouped[tag] += 1
            if len(examples[tag]) < 5:
                examples[tag].append(page['slug'])

    rows = []
    for tag, count in grouped.most_common():
        if count < 5:
            continue
        represented = tag in existing
        score = count - (5 if represented else 0)
        if score <= 0:
            continue
        rows.append({
            'theme': tag,
            'score': score,
            'summary_pages': count,
            'represented': represented,
            'examples': examples[tag],
        })
    return sorted(rows, key=lambda item: (-item['score'], item['theme']))[:25]


def load_alias_values():
    aliases = {}
    if not TAG_ALIASES.exists():
        return aliases
    current = None
    for line in TAG_ALIASES.read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        if not line.startswith(' ') and ':' in line:
            current = line.split(':', 1)[0].strip()
            aliases.setdefault(current, [])
        elif current and line.strip().startswith('- '):
            aliases[current].append(line.strip()[2:].strip())
    return aliases


def tag_normalization_candidates(pages):
    tag_counts = Counter(tag for page in pages for tag in page['tags'])
    known_aliases = load_alias_values()
    alias_values = {alias for values in known_aliases.values() for alias in values}
    candidates = []
    for tag, count in tag_counts.items():
        if tag in alias_values:
            canonical = next(k for k, values in known_aliases.items() if tag in values)
            candidates.append({'tag': tag, 'count': count, 'suggestion': canonical, 'reason': 'known alias'})

    by_norm = defaultdict(list)
    for tag, count in tag_counts.items():
        if not tag.startswith('topic/'):
            continue
        normalized = tag.lower().replace('_', '-').replace(' ', '-').replace('microsoft-', '').replace('ms-', '')
        normalized = normalized.replace('defender-for-', 'defender-')
        by_norm[normalized].append((tag, count))
    for group in by_norm.values():
        if len(group) <= 1:
            continue
        lowercase_tags = [item for item in group if item[0] == item[0].lower()]
        canonical = max(lowercase_tags or group, key=lambda item: item[1])[0]
        for tag, count in group:
            if tag != canonical:
                candidates.append({'tag': tag, 'count': count, 'suggestion': canonical, 'reason': 'similar topic spelling'})
    return sorted(candidates, key=lambda item: (-item['count'], item['tag']))[:30]


def load_output_linked_pages():
    linked = set()
    for path in OUTPUTS_ROOT.rglob('*.md'):
        try:
            content = path.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        linked.update(WIKILINK_RE.findall(content))
    return linked


def raw_quality_grades(pages):
    grade_rank = {'registered': 1, 'summarized': 2, 'linked': 3, 'synthesized': 4, 'output-used': 5}
    raw_best = {}
    raw_pages = defaultdict(list)
    output_linked_pages = load_output_linked_pages()
    for page in pages:
        if page['slug'] in output_linked_pages:
            grade = 'output-used'
        elif page['category'] == 'synthesis':
            grade = 'synthesized'
        elif page['category'] in ('entities', 'concepts'):
            grade = 'linked'
        elif page['category'] == 'summaries' and page['is_registry']:
            grade = 'registered'
        elif page['category'] == 'summaries':
            grade = 'summarized'
        else:
            grade = 'linked'
        for raw_ref in page['raw_refs']:
            raw_pages[raw_ref].append(page['slug'])
            if raw_ref not in raw_best or grade_rank[grade] > grade_rank[raw_best[raw_ref]]:
                raw_best[raw_ref] = grade

    counts = Counter(raw_best.values())
    registered_groups = Counter()
    for raw_ref, grade in raw_best.items():
        if grade != 'registered':
            continue
        parts = raw_ref.split('/')
        key = '/'.join(parts[:3]) if len(parts) >= 3 else raw_ref
        registered_groups[key] += 1
    return counts, registered_groups.most_common(20)


def graph_registry_hints(pages):
    registry_slugs = {page['slug'] for page in pages if page['is_registry']}
    if not GRAPH_JSON.exists():
        return []
    graph = json.loads(GRAPH_JSON.read_text(encoding='utf-8'))
    degree = Counter()
    for edge in graph.get('edges', graph.get('links', [])):
        src = edge.get('from') or edge.get('source')
        dst = edge.get('to') or edge.get('target')
        if src:
            degree[src] += 1
        if dst:
            degree[dst] += 1
    rows = []
    for slug_name, deg in degree.most_common():
        if slug_name in registry_slugs and deg >= 20:
            rows.append({'page': slug_name, 'degree': deg, 'hint': 'search/rerank에서 downrank 또는 filter 토글'})
    return rows[:20]


def render_report(data):
    today = date.today().isoformat()
    lines = [
        '---', 'title: "Wiki Action Queue"', 'type: report', f'updated: {today}', '---', '',
        f'# Wiki Action Queue — {today}', '',
        '> qmd 제외. 기존 lint가 통과한 저장소에서 다음 큐레이션/구조 개선 후보를 자동 선별한다.', '',
        '## 1. Source Registry 승격 후보', '',
        '| 순위 | 후보 페이지 | 점수 | Sources | 그룹 | 근거 |',
        '|---:|---|---:|---:|---:|---|',
    ]
    for i, item in enumerate(data['registry_promotion_candidates'][:20], 1):
        lines.append(f"| {i} | [[{md_cell(item['page'])}]] | {item['score']} | {item['sources']} | {item.get('group_size', 1)} | {md_cell(item['signals'])} |")
    if not data['registry_promotion_candidates']:
        lines.append('| - | - | - | - | - | 후보 없음 |')

    lines += ['', '## 2. Synthesis 후보 테마', '', '| 순위 | 테마 | 점수 | Summary pages | 예시 |', '|---:|---|---:|---:|---|']
    for i, item in enumerate(data['synthesis_candidates'][:20], 1):
        examples = ', '.join(f"[[{example}]]" for example in item['examples'][:3])
        lines.append(f"| {i} | `{item['theme']}` | {item['score']} | {item['summary_pages']} | {examples} |")
    if not data['synthesis_candidates']:
        lines.append('| - | - | - | - | 후보 없음 |')

    lines += ['', '## 3. 태그 정규화 후보', '', '| 태그 | 사용 수 | 제안 | 이유 |', '|---|---:|---|---|']
    for item in data['tag_normalization_candidates'][:20]:
        lines.append(f"| `{item['tag']}` | {item['count']} | `{item['suggestion']}` | {item['reason']} |")
    if not data['tag_normalization_candidates']:
        lines.append('| - | - | - | 후보 없음 |')

    lines += ['', '## 4. Raw 지식화 등급', '', '| 등급 | Raw 파일 수 | 의미 |', '|---|---:|---|']
    meanings = {
        'registered': 'source registry에만 등록됨',
        'summarized': 'curated summary에서 인용됨',
        'linked': 'entity/concept까지 연결됨',
        'synthesized': 'synthesis 레이어까지 활용됨',
        'output-used': 'outputs 산출물까지 사용됨',
    }
    for grade in ('registered', 'summarized', 'linked', 'synthesized', 'output-used'):
        lines.append(f"| `{grade}` | {data['raw_quality_counts'].get(grade, 0)} | {meanings[grade]} |")

    lines += ['', '### Registered-only 상위 raw 그룹', '', '| Raw 그룹 | 파일 수 | 다음 액션 |', '|---|---:|---|']
    for group, count in data['registered_only_groups'][:15]:
        lines.append(f'| `{md_cell(group)}` | {count} | 상위 파일 샘플링 후 summary 승격 여부 판단 |')
    if not data['registered_only_groups']:
        lines.append('| - | - | 후보 없음 |')

    lines += ['', '## 5. Graph/Search 랭킹 힌트', '', '| 페이지 | Degree | 권장 처리 |', '|---|---:|---|']
    for item in data['graph_registry_hints']:
        lines.append(f"| [[{md_cell(item['page'])}]] | {item['degree']} | {item['hint']} |")
    if not data['graph_registry_hints']:
        lines.append('| - | - | 후보 없음 |')

    lines += ['', '## 6. 다음 실행 순서', '', '1. Source Registry 승격 후보 Top 5에서 실제 가치가 높은 페이지를 curated summary로 작성한다.', '2. Synthesis 후보 Top 3는 기존 synthesis와 중복 여부를 확인한 뒤 종합 페이지로 승격한다.', '3. 태그 정규화 후보는 `scripts/tag-aliases.yml`에 추가 후 `scripts/migrate-tags.py`로 일괄 적용한다.', '4. Graph/Search 랭킹 힌트의 registry hub는 질의 rerank에서 감점하거나 필터링한다.', '']
    return '\n'.join(lines)


def main():
    pages = load_pages()
    raw_counts, registered_groups = raw_quality_grades(pages)
    data = {
        'generated': date.today().isoformat(),
        'registry_promotion_candidates': registry_promotion_candidates(pages),
        'synthesis_candidates': synthesis_candidates(pages),
        'tag_normalization_candidates': tag_normalization_candidates(pages),
        'raw_quality_counts': dict(raw_counts),
        'registered_only_groups': registered_groups,
        'graph_registry_hints': graph_registry_hints(pages),
    }
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(render_report(data), encoding='utf-8')
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Registry promotion candidates: {len(data['registry_promotion_candidates'])}")
    print(f"Synthesis candidates: {len(data['synthesis_candidates'])}")
    print(f"Tag normalization candidates: {len(data['tag_normalization_candidates'])}")
    print(f"Report: {OUT_MD}")


if __name__ == '__main__':
    main()
