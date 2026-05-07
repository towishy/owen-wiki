"""Query wiki pages with repository-native ranking signals."""
import argparse
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from wiki_utils import ROOT, WIKI_ROOT, OUTPUTS_ROOT, extract_wikilink_targets, iter_wiki_pages, md_cell, tokenize

GRAPH_JSON = ROOT / 'graphify-out' / 'graph.json'
ONTOLOGY_JSONL = OUTPUTS_ROOT / 'wiki-ops' / 'ontology-sidecar.jsonl'
OUT_DIR = OUTPUTS_ROOT / 'wiki-ops' / 'query-runs'

DAMPING = 0.85
EPS = 1e-6
MAX_ITER = 100

CATEGORY_BOOST = {
    'synthesis': 4.0,
    'entities': 3.0,
    'concepts': 3.0,
    'comparisons': 2.0,
    'summaries': 1.5,
    'ontology': 0.5,
    '_root': 0.0,
}


def query_rank_multiplier(page_id):
    if page_id == 'remaining-raw-source-registry-hub':
        return 0.20, 'registry-hub'
    if page_id.startswith('remaining-raw-'):
        return 0.35, 'registry-page'
    if page_id.endswith('-ontology') or page_id == 'full-wiki-ontology':
        return 0.55, 'ontology-meta'
    if page_id in {'ms-korea-microsoft-documents-hub', 'onsite-reports-content-hub', 'owen-knowledge-base'}:
        return 0.10, 'mega-source-hub'
    return 1.00, 'curated-default'


def load_graph():
    if not GRAPH_JSON.exists():
        return [], []
    graph = json.loads(GRAPH_JSON.read_text(encoding='utf-8'))
    nodes = [node.get('id') or node.get('label') for node in graph.get('nodes', [])]
    edges = graph.get('edges', graph.get('links', []))
    return nodes, edges


def pagerank(nodes, edges):
    if not nodes:
        return {}
    node_set = set(nodes)
    out_links = {node: [] for node in nodes}
    in_links = {node: [] for node in nodes}
    for edge in edges:
        source = edge.get('from') or edge.get('source')
        target = edge.get('to') or edge.get('target')
        if source in node_set and target in node_set:
            out_links[source].append(target)
            in_links[target].append(source)
    scores = {node: 1.0 / len(nodes) for node in nodes}
    for _ in range(MAX_ITER):
        dangling = sum(scores[node] for node in nodes if not out_links[node])
        updated = {}
        for node in nodes:
            inbound = sum(scores[source] / len(out_links[source]) for source in in_links[node] if out_links[source])
            updated[node] = (1 - DAMPING) / len(nodes) + DAMPING * (inbound + dangling / len(nodes))
        diff = sum(abs(updated[node] - scores[node]) for node in nodes)
        scores = updated
        if diff < EPS:
            break
    return scores


def ontology_signals():
    counts = Counter()
    neighbors = defaultdict(set)
    if not ONTOLOGY_JSONL.exists():
        return counts, neighbors
    for line in ONTOLOGY_JSONL.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        source = record.get('source')
        target = record.get('target')
        weight = float(record.get('weight') or 0.6)
        if source:
            counts[source] += weight
        if target:
            counts[target] += weight
        if source and target:
            neighbors[source].add(target)
            neighbors[target].add(source)
    return counts, neighbors


def load_pages():
    pages = []
    for page in iter_wiki_pages():
        if page['category'] not in {'entities', 'concepts', 'summaries', 'comparisons', 'synthesis', 'ontology'}:
            continue
        haystack = ' '.join([
            page['slug'],
            str(page['title']),
            ' '.join(page['tags']),
            page['body'],
        ])
        pages.append(page | {
            'tokens': Counter(tokenize(haystack)),
            'links': set(extract_wikilink_targets(page['body'])),
        })
    return pages


def score_pages(query, limit):
    query_tokens = tokenize(query)
    if not query_tokens:
        raise SystemExit('Query must include at least one searchable token.')
    nodes, edges = load_graph()
    pr = pagerank(nodes, edges)
    ontology_counts, ontology_neighbors = ontology_signals()
    max_pr = max(pr.values()) if pr else 1.0
    max_ontology = max(ontology_counts.values()) if ontology_counts else 1.0
    results = []
    for page in load_pages():
        token_score = 0.0
        for token in query_tokens:
            if token in page['slug'].lower():
                token_score += 8.0
            if token in str(page['title']).lower():
                token_score += 6.0
            if any(token in tag.lower() for tag in page['tags']):
                token_score += 4.0
            token_score += min(page['tokens'].get(token, 0), 12) * 0.7
        if token_score <= 0:
            continue
        multiplier, reason = query_rank_multiplier(page['slug'])
        raw_pr = pr.get(page['slug'], 0.0)
        pagerank_score = (raw_pr / max_pr) * 5.0 * multiplier if max_pr else 0.0
        ontology_score = (ontology_counts.get(page['slug'], 0.0) / max_ontology) * 3.0 if max_ontology else 0.0
        category_score = CATEGORY_BOOST.get(page['category'], 0.0)
        final_score = token_score + pagerank_score + ontology_score + category_score
        results.append({
            'page': page['slug'],
            'path': page['path'],
            'title': page['title'],
            'category': page['category'],
            'score': round(final_score, 3),
            'token_score': round(token_score, 3),
            'category_score': round(category_score, 3),
            'pagerank_score': round(pagerank_score, 3),
            'ontology_score': round(ontology_score, 3),
            'raw_pagerank': round(raw_pr, 8),
            'query_multiplier': multiplier,
            'rank_reason': reason,
            'ontology_neighbors': sorted(ontology_neighbors.get(page['slug'], set()))[:8],
        })
    return sorted(results, key=lambda item: (-item['score'], item['page']))[:limit]


def render_markdown(query, results):
    today = date.today().isoformat()
    lines = [
        '---',
        'title: "Wiki Query Result"',
        'type: report',
        f'updated: {today}',
        '---',
        '',
        f'# Wiki Query Result — {query}',
        '',
        '| Rank | Page | Category | Score | Token | PageRank | Ontology | Reason |',
        '|---:|---|---|---:|---:|---:|---:|---|',
    ]
    for rank, item in enumerate(results, 1):
        lines.append(
            f"| {rank} | [[{md_cell(item['page'])}]] | `{item['category']}` | {item['score']:.3f} | {item['token_score']:.3f} | {item['pagerank_score']:.3f} | {item['ontology_score']:.3f} | `{item['rank_reason']}` |"
        )
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description='Rank wiki pages for a natural-language query.')
    parser.add_argument('query', help='Query text')
    parser.add_argument('--limit', type=int, default=10, help='Number of results')
    parser.add_argument('--json', action='store_true', help='Print JSON')
    parser.add_argument('--write-report', action='store_true', help='Write outputs/wiki-ops/query-runs report')
    args = parser.parse_args()
    results = score_pages(args.query, args.limit)
    payload = {'query': args.query, 'updated': date.today().isoformat(), 'results': results}
    if args.write_report:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        slug = '-'.join(tokenize(args.query)[:8]) or 'query'
        (OUT_DIR / f'{slug}.md').write_text(render_markdown(args.query, results), encoding='utf-8')
        (OUT_DIR / f'{slug}.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f'Query: {args.query}')
    for rank, item in enumerate(results, 1):
        print(f"{rank:>2}. {item['page']} [{item['category']}] score={item['score']:.3f} reason={item['rank_reason']}")


if __name__ == '__main__':
    main()