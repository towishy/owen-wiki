"""Update canonical metrics snippets in README.md and AGENTS.md."""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
README = ROOT / 'README.md'
AGENTS = ROOT / 'AGENTS.md'
REPO_METRICS = ROOT / 'outputs' / 'wiki-ops' / 'repo-metrics.json'
RELATION_QUALITY = ROOT / 'outputs' / 'wiki-ops' / 'ontology-relation-quality.json'
GRAPH_JSON = ROOT / 'graphify-out' / 'graph.json'
GRAPH_REPORT = ROOT / 'graphify-out' / 'GRAPH_REPORT.md'


def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8'))


def fmt(number):
    return f'{int(number):,}'


def graph_metrics():
    graph = load_json(GRAPH_JSON, {'nodes': [], 'edges': []})
    communities = 0
    if GRAPH_REPORT.exists():
        match = re.search(r'\| 커뮤니티 \(Louvain\) \|\s*([0-9,]+)\s*\|', GRAPH_REPORT.read_text(encoding='utf-8', errors='replace'))
        if match:
            communities = int(match.group(1).replace(',', ''))
    return {'nodes': len(graph.get('nodes', [])), 'edges': len(graph.get('edges', graph.get('links', []))), 'communities': communities}


def metrics():
    repo = load_json(REPO_METRICS, {})
    relation = load_json(RELATION_QUALITY, {})
    graph = graph_metrics()
    return repo, relation, graph


def readme_snippet(repo, relation, graph):
    pages = repo.get('pages', {})
    content = repo.get('content', {})
    tags = repo.get('tags', {})
    raw = repo.get('raw_sources', {})
    tag_groups = tags.get('groups', {})
    return '\n'.join([
        '| 항목 | 수치 |',
        '|------|-----:|',
        f"| 위키 페이지 | **{fmt(pages.get('total', 0))}** |",
        f"| 온톨로지 파일 | {pages.get('ontology', 0)} |",
        f"| 총 라인 수 | {fmt(content.get('total_lines', 0))} |",
        f"| 총 단어 수 | {fmt(content.get('total_words', 0))} |",
        f"| 위키링크 | **{fmt(content.get('wikilinks', 0))}** (페이지당 평균 {content.get('avg_links_per_page', 0)}) |",
        f"| 태그 | {fmt(tags.get('unique', 0))}종 (`prod/` {tag_groups.get('prod', {}).get('unique', 0)} · `customer/` {tag_groups.get('customer', {}).get('unique', 0)} · `topic/` {tag_groups.get('topic', {}).get('unique', 0)} · `type/` {tag_groups.get('type', {}).get('unique', 0)} · `series/` {tag_groups.get('series', {}).get('unique', 0)}) |",
        f"| Raw 소스 파일 | **{fmt(raw.get('files', 0))}** ({raw.get('size_gb', 0)} GB) |",
        f"| 온톨로지 관계 | **{fmt(relation.get('relations', 0))}** (`related-to` {relation.get('weak_related_to_count', 0)}, strict sidecar 기준) |",
        f"| Git 커밋 | {fmt(repo.get('git', {}).get('commits', 0))}+ |",
        '',
        '### 그래프 (graphify-out)',
        '',
        '| 항목 | 값 |',
        '|------|---:|',
        f"| 노드 (페이지) | {fmt(graph['nodes'])} |",
        f"| 엣지 (위키링크) | {fmt(graph['edges'])} |",
        f"| 커뮤니티 (Louvain) | {graph['communities']} |",
        '| 연결 컴포넌트 | 1 |',
        '| 고아 노드 | **0** |',
        '| 깨진 링크 | **0** |',
    ])


def agents_snippet(repo, relation, graph):
    pages = repo.get('pages', {})
    categories = pages.get('categories', {})
    content = repo.get('content', {})
    tags = repo.get('tags', {})
    tag_groups = tags.get('groups', {})
    confidence = repo.get('confidence', {})
    raw = repo.get('raw_sources', {})
    category_summary = ' / '.join(
        f"{name} {count}" for name, count in categories.items()
    )
    return '\n'.join([
        f"- raw/ 전체: {fmt(raw.get('files', 0))} 인덱싱 파일 ({raw.get('size_gb', 0)} GB)",
        f"- wiki/ 페이지: **{fmt(pages.get('total', 0))}** ({category_summary} / ontology {pages.get('ontology', 0)})",
        f"- 위키링크: {fmt(content.get('wikilinks', 0))}개 (페이지당 평균 {content.get('avg_links_per_page', 0)})",
        f"- 온톨로지 관계: {fmt(relation.get('relations', 0))}개 (`related-to` {relation.get('weak_related_to_count', 0)}개, strict sidecar 후)",
        f"- 태그: {fmt(tags.get('unique', 0))}종 (prod/ {tag_groups.get('prod', {}).get('unique', 0)} · customer/ {tag_groups.get('customer', {}).get('unique', 0)} · topic/ {tag_groups.get('topic', {}).get('unique', 0)} · type/ {tag_groups.get('type', {}).get('unique', 0)} · series/ {tag_groups.get('series', {}).get('unique', 0)})",
        f"- Confidence 분포: 0.95+ {confidence.get('0.95-1.0', 0)} / 0.80–0.94 {confidence.get('0.80-0.94', 0)} / 0.65–0.79 {confidence.get('0.65-0.79', 0)} / 0.40–0.64 {confidence.get('0.40-0.64', 0)} / unset {confidence.get('unset', 0)}",
        '- 2-tier 인덱스: `index.md` (허브) + 카테고리별 `_index.md` 6개 (entities/concepts/summaries/comparisons/synthesis/ontology)',
        f"- Git 커밋: {fmt(repo.get('git', {}).get('commits', 0))}개+",
        f"- 그래프(graphify-out): 노드 {fmt(graph['nodes'])} · 엣지 {fmt(graph['edges'])} · 커뮤니티 {graph['communities']} · 고아 0 · 깨진 링크 0",
        '- Canonical 운영 지표: `outputs/wiki-ops/wiki-ops-dashboard.json`, 저장소 규모 지표: `outputs/wiki-ops/repo-metrics.json`',
        '- index.md 허브 → 카테고리 _index.md → wiki/ontology/ 기반 구조 분석을 병행한다',
    ])


def replace_block(text, marker, replacement):
    start = f'<!-- wiki-metrics:{marker}:start -->'
    end = f'<!-- wiki-metrics:{marker}:end -->'
    pattern = re.compile(re.escape(start) + r'.*?' + re.escape(end), re.DOTALL)
    block = f'{start}\n{replacement}\n{end}'
    if pattern.search(text):
        return pattern.sub(block, text)
    raise SystemExit(f'Missing metrics block marker: {marker}')


def main():
    parser = argparse.ArgumentParser(description='Update README/AGENTS metric snippets.')
    parser.add_argument('--check', action='store_true', help='Fail if snippets are stale')
    args = parser.parse_args()
    repo, relation, graph = metrics()
    updates = {
        README: ('readme', readme_snippet(repo, relation, graph)),
        AGENTS: ('agents', agents_snippet(repo, relation, graph)),
    }
    changed = []
    for path, (marker, snippet) in updates.items():
        old = path.read_text(encoding='utf-8')
        new = replace_block(old, marker, snippet)
        if new != old:
            changed.append(path)
            if not args.check:
                path.write_text(new, encoding='utf-8')
    if args.check and changed:
        for path in changed:
            print(f'[STALE] {path.relative_to(ROOT)}')
        sys.exit(1)
    print(f'Metrics snippets updated: {len(changed)}')


if __name__ == '__main__':
    main()