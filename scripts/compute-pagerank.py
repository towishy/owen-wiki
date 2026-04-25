"""Compute PageRank on wiki graph to identify hub/authority pages.

Input: graphify-out/graph.json (wiki-graph-viz.py가 생성한 그래프)
Output: outputs/drafts/wiki-pagerank.md (Top 30 허브)

NetworkX 미설치 시 자체 power iteration 구현 사용 (의존성 0).
"""
import json
import sys
from pathlib import Path
from datetime import date

ROOT = Path(__file__).parent.parent
GRAPH_JSON = ROOT / 'graphify-out' / 'graph.json'
OUT_REPORT = ROOT / 'outputs' / 'drafts' / 'wiki-pagerank.md'

DAMPING = 0.85
EPS = 1e-6
MAX_ITER = 100


def load_graph():
    if not GRAPH_JSON.exists():
        print(f'graph.json not found at {GRAPH_JSON}')
        print('Run: python scripts/wiki-graph-viz.py first')
        sys.exit(1)
    return json.loads(GRAPH_JSON.read_text(encoding='utf-8'))


def pagerank(nodes, edges):
    n = len(nodes)
    if n == 0:
        return {}
    idx = {nid: i for i, nid in enumerate(nodes)}
    out_links = {nid: [] for nid in nodes}
    in_links = {nid: [] for nid in nodes}
    for e in edges:
        src = e.get('from') or e.get('source')
        dst = e.get('to') or e.get('target')
        if src in idx and dst in idx:
            out_links[src].append(dst)
            in_links[dst].append(src)

    pr = {nid: 1.0 / n for nid in nodes}
    for it in range(MAX_ITER):
        new_pr = {}
        dangling = sum(pr[nid] for nid in nodes if not out_links[nid])
        for nid in nodes:
            s = sum(pr[src] / len(out_links[src]) for src in in_links[nid] if out_links[src])
            new_pr[nid] = (1 - DAMPING) / n + DAMPING * (s + dangling / n)
        diff = sum(abs(new_pr[nid] - pr[nid]) for nid in nodes)
        pr = new_pr
        if diff < EPS:
            break
    return pr


def main():
    graph = load_graph()
    nodes_data = graph.get('nodes', [])
    edges_data = graph.get('edges', graph.get('links', []))
    nodes = [n.get('id') or n.get('label') for n in nodes_data]
    label_map = {(n.get('id') or n.get('label')): n.get('label', n.get('id')) for n in nodes_data}
    pr = pagerank(nodes, edges_data)

    ranked = sorted(pr.items(), key=lambda kv: -kv[1])[:30]
    today = date.today().isoformat()
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        '---', 'title: "Wiki PageRank Top 30 (허브 페이지)"', 'type: report',
        f'updated: {today}', '---', '',
        f'# Wiki PageRank Top 30 — {len(nodes)} nodes / {len(edges_data)} edges',
        '',
        '> 인바운드 링크 가중 + 재귀 전파. 위키의 구조적 허브를 식별.',
        '',
        '| 순위 | 페이지 | PageRank |',
        '|------|--------|----------|',
    ]
    for i, (nid, score) in enumerate(ranked, 1):
        label = label_map.get(nid, nid)
        lines.append(f'| {i} | [[{label}]] | {score:.5f} |')
    OUT_REPORT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'Top 5 hubs:')
    for i, (nid, score) in enumerate(ranked[:5], 1):
        print(f'  {i}. {label_map.get(nid, nid)}: {score:.5f}')
    print(f'\nReport: {OUT_REPORT}')


if __name__ == '__main__':
    main()
