"""Generate graph delta report against a git ref."""
import argparse
import json
import subprocess
from collections import Counter
from datetime import date

from wiki_utils import OUTPUTS_ROOT, ROOT

GRAPH_JSON = ROOT / 'graphify-out' / 'graph.json'
OUT_JSON = OUTPUTS_ROOT / 'wiki-ops' / 'graph-delta.json'
OUT_MD = OUTPUTS_ROOT / 'wiki-ops' / 'graph-delta.md'


def load_current():
    return json.loads(GRAPH_JSON.read_text(encoding='utf-8'))


def load_from_git(ref):
    result = subprocess.run(['git', 'show', f'{ref}:graphify-out/graph.json'], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode != 0:
        return {'nodes': [], 'edges': []}
    return json.loads(result.stdout)


def summarize(graph):
    nodes = [node.get('id') or node.get('label') for node in graph.get('nodes', [])]
    edges = graph.get('edges', graph.get('links', []))
    degree = Counter()
    for edge in edges:
        source = edge.get('from') or edge.get('source')
        target = edge.get('to') or edge.get('target')
        if source:
            degree[source] += 1
        if target:
            degree[target] += 1
    return {'nodes': set(nodes), 'edges': edges, 'degree': degree}


def build_delta(base_ref):
    base = summarize(load_from_git(base_ref))
    current = summarize(load_current())
    added_nodes = sorted(current['nodes'] - base['nodes'])
    removed_nodes = sorted(base['nodes'] - current['nodes'])
    top_degree_delta = []
    for node in sorted(current['nodes'] | base['nodes']):
        delta = current['degree'].get(node, 0) - base['degree'].get(node, 0)
        if delta:
            top_degree_delta.append({'page': node, 'delta': delta, 'current_degree': current['degree'].get(node, 0), 'base_degree': base['degree'].get(node, 0)})
    top_degree_delta.sort(key=lambda item: (-abs(item['delta']), item['page']))
    return {
        'updated': date.today().isoformat(),
        'base_ref': base_ref,
        'current': {'nodes': len(current['nodes']), 'edges': len(current['edges'])},
        'base': {'nodes': len(base['nodes']), 'edges': len(base['edges'])},
        'delta': {'nodes': len(current['nodes']) - len(base['nodes']), 'edges': len(current['edges']) - len(base['edges'])},
        'added_nodes': added_nodes[:50],
        'removed_nodes': removed_nodes[:50],
        'top_degree_delta': top_degree_delta[:30],
    }


def latest_tag():
    result = subprocess.run(['git', 'describe', '--tags', '--abbrev=0'], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return 'HEAD~1'


def render(payload):
    lines = [
        '---', 'title: "Graph Delta"', 'type: report', f"updated: {payload['updated']}", '---', '',
        f"# Graph Delta — {payload['base_ref']} → working tree", '',
        '| Metric | Base | Current | Delta |', '|---|---:|---:|---:|',
        f"| Nodes | {payload['base']['nodes']} | {payload['current']['nodes']} | {payload['delta']['nodes']:+d} |",
        f"| Edges | {payload['base']['edges']} | {payload['current']['edges']} | {payload['delta']['edges']:+d} |",
        '', '## Added Nodes', '', '| Page |', '|---|',
    ]
    for node in payload['added_nodes'][:30]:
        lines.append(f'| [[{node}]] |')
    if not payload['added_nodes']:
        lines.append('| - |')
    lines += ['', '## Removed Nodes', '', '| Page |', '|---|']
    for node in payload['removed_nodes'][:30]:
        lines.append(f'| [[{node}]] |')
    if not payload['removed_nodes']:
        lines.append('| - |')
    lines += ['', '## Degree Delta', '', '| Page | Base | Current | Delta |', '|---|---:|---:|---:|']
    for item in payload['top_degree_delta'][:20]:
        lines.append(f"| [[{item['page']}]] | {item['base_degree']} | {item['current_degree']} | {item['delta']:+d} |")
    if not payload['top_degree_delta']:
        lines.append('| - | - | - | - |')
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description='Generate graph delta report.')
    parser.add_argument('--base-ref', default='', help='Git ref to compare graphify-out/graph.json against; defaults to latest tag')
    args = parser.parse_args()
    payload = build_delta(args.base_ref or latest_tag())
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    OUT_MD.write_text(render(payload), encoding='utf-8')
    print(f"Graph delta nodes: {payload['delta']['nodes']:+d}")
    print(f"Graph delta edges: {payload['delta']['edges']:+d}")
    print(f'Report: {OUT_MD}')


if __name__ == '__main__':
    main()