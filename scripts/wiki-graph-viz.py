#!/usr/bin/env python3
"""wiki-graph-viz.py — 위키 전체 위키링크 그래프 시각화

wiki/ 폴더의 모든 .md 파일에서 [[위키링크]]를 파싱하여
NetworkX 그래프를 구축하고, Louvain 커뮤니티 탐지 후
인터랙티브 HTML + 텍스트 보고서를 생성한다.

사용법:
    python scripts/wiki-graph-viz.py [--wiki-dir wiki] [--out-dir graphify-out]
"""

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime

import networkx as nx
from community import community_louvain  # python-louvain
from pyvis.network import Network

# ── 설정 ──────────────────────────────────────────────

WIKILINK_RE = re.compile(r"\[\[([^\]\|#]+)(?:[#\|][^\]]*)?\]\]")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
YAML_FIELD_RE = re.compile(r"^(\w[\w_-]*):\s*(.+)$", re.MULTILINE)

# 카테고리별 노드 색상
CATEGORY_COLORS = {
    "entities": "#4CAF50",     # 초록
    "concepts": "#2196F3",     # 파랑
    "summaries": "#FF9800",    # 주황
    "comparisons": "#9C27B0",  # 보라
    "synthesis": "#F44336",    # 빨강
    "ontology": "#607D8B",     # 회색
    "_unknown": "#9E9E9E",     # 기본 회색
}

# 커뮤니티별 색상 팔레트
COMMUNITY_PALETTE = [
    "#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231",
    "#911eb4", "#42d4f4", "#f032e6", "#bfef45", "#fabebe",
    "#469990", "#e6beff", "#9A6324", "#fffac8", "#800000",
    "#aaffc3", "#808000", "#ffd8b1", "#000075", "#a9a9a9",
]


def parse_frontmatter(text: str) -> dict:
    """YAML 프론트매터에서 주요 필드 추출 (정규식 기반, yaml 의존성 없음)."""
    meta = {}
    m = FRONTMATTER_RE.match(text)
    if not m:
        return meta
    block = m.group(1)
    for fm in YAML_FIELD_RE.finditer(block):
        key, val = fm.group(1), fm.group(2).strip().strip('"').strip("'")
        meta[key] = val
    return meta


def extract_wikilinks(text: str) -> list[str]:
    """마크다운에서 [[위키링크]] 추출. 코드블록·YAML 내부 제외."""
    # 코드블록 제거
    cleaned = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # YAML 프론트매터 제거
    cleaned = re.sub(r"^---\s*\n.*?\n---", "", cleaned, flags=re.DOTALL)
    return WIKILINK_RE.findall(cleaned)


def detect_category(filepath: Path, wiki_dir: Path) -> str:
    """파일 경로에서 위키 카테고리 추출."""
    try:
        rel = filepath.relative_to(wiki_dir)
        parts = rel.parts
        if len(parts) >= 2:
            return parts[0]
    except ValueError:
        pass
    return "_unknown"


def build_graph(wiki_dir: Path) -> tuple[nx.DiGraph, dict]:
    """wiki/ 폴더에서 방향 그래프 구축. 노드 = 페이지, 엣지 = 위키링크."""
    G = nx.DiGraph()
    page_meta = {}  # stem -> metadata

    md_files = sorted(wiki_dir.rglob("*.md"))
    for fpath in md_files:
        if fpath.name.startswith("_"):
            continue  # _index.md 제외

        stem = fpath.stem
        text = fpath.read_text(encoding="utf-8", errors="replace")
        meta = parse_frontmatter(text)
        category = detect_category(fpath, wiki_dir)

        meta["_category"] = category
        meta["_path"] = str(fpath.relative_to(wiki_dir.parent))
        page_meta[stem] = meta

        # 노드 추가
        if not G.has_node(stem):
            G.add_node(stem, category=category)

        # 위키링크 → 엣지
        links = extract_wikilinks(text)
        seen = set()
        for link in links:
            target = link.strip()
            if target and target != stem and target not in seen:
                seen.add(target)
                if not G.has_node(target):
                    G.add_node(target, category="_unknown")
                G.add_edge(stem, target)

    return G, page_meta


def analyze_graph(G: nx.DiGraph, page_meta: dict) -> dict:
    """그래프 분석: 커뮤니티, god nodes, orphans, surprise edges."""
    result = {}

    # 기본 통계
    result["nodes"] = G.number_of_nodes()
    result["edges"] = G.number_of_edges()

    # 무방향 변환 (커뮤니티 탐지용)
    U = G.to_undirected()

    # Louvain 커뮤니티
    partition = community_louvain.best_partition(U, random_state=42)
    result["partition"] = partition
    n_communities = len(set(partition.values()))
    result["n_communities"] = n_communities

    # 커뮤니티별 노드
    communities = defaultdict(list)
    for node, comm_id in partition.items():
        communities[comm_id].append(node)
    result["communities"] = dict(communities)

    # Degree 중심성 (방향 그래프의 in-degree + out-degree)
    degree = dict(G.degree())
    in_degree = dict(G.in_degree())
    top_nodes = sorted(degree.items(), key=lambda x: x[1], reverse=True)[:20]
    result["god_nodes"] = top_nodes
    result["in_degree_top"] = sorted(in_degree.items(), key=lambda x: x[1], reverse=True)[:20]

    # 고아 노드 (degree == 0)
    orphans = [n for n, d in degree.items() if d == 0]
    result["orphans"] = orphans

    # 단독 인바운드 0 노드 (wiki 안에 존재하지만 아무도 링크하지 않음)
    no_inbound = [n for n, d in in_degree.items() if d == 0 and n in page_meta]
    result["no_inbound"] = no_inbound

    # Surprise edges: 서로 다른 커뮤니티 간 엣지 (가중치 = 커뮤니티 거리)
    cross_edges = []
    for u, v in G.edges():
        cu = partition.get(u, -1)
        cv = partition.get(v, -1)
        if cu != cv and cu >= 0 and cv >= 0:
            cross_edges.append((u, v, cu, cv))
    result["cross_community_edges"] = len(cross_edges)

    # 가장 연결이 적은 커뮤니티 쌍 → surprise
    pair_count = Counter()
    for _, _, cu, cv in cross_edges:
        pair_count[tuple(sorted([cu, cv]))] += 1
    rare_pairs = pair_count.most_common()[-10:] if pair_count else []
    result["rare_community_pairs"] = rare_pairs

    # Betweenness centrality (상위 10)
    bc = nx.betweenness_centrality(U, k=min(100, len(U)))
    result["betweenness_top"] = sorted(bc.items(), key=lambda x: x[1], reverse=True)[:10]

    # 연결 컴포넌트
    components = list(nx.connected_components(U))
    result["n_components"] = len(components)
    result["largest_component"] = len(max(components, key=len)) if components else 0

    return result


def build_html(G: nx.DiGraph, analysis: dict, page_meta: dict, out_path: Path):
    """pyvis로 인터랙티브 HTML 그래프 생성."""
    net = Network(
        height="900px",
        width="100%",
        bgcolor="#1a1a2e",
        font_color="white",
        directed=True,
        notebook=False,
    )

    partition = analysis["partition"]
    degree = dict(G.degree())

    for node in G.nodes():
        comm = partition.get(node, 0)
        color = COMMUNITY_PALETTE[comm % len(COMMUNITY_PALETTE)]
        d = degree.get(node, 0)
        size = max(8, min(50, 8 + d * 1.5))

        meta = page_meta.get(node, {})
        cat = meta.get("_category", G.nodes[node].get("category", "?"))
        title_field = meta.get("title", node)
        conf = meta.get("confidence", "?")

        tooltip = (
            f"<b>{title_field}</b><br>"
            f"Category: {cat}<br>"
            f"Community: {comm}<br>"
            f"Degree: {d} (in:{G.in_degree(node)} / out:{G.out_degree(node)})<br>"
            f"Confidence: {conf}"
        )

        label = node if d >= 5 else ""

        net.add_node(
            node,
            label=label,
            title=tooltip,
            size=size,
            color=color,
            borderWidth=2,
            borderWidthSelected=4,
        )

    for u, v in G.edges():
        net.add_edge(u, v, color="rgba(255,255,255,0.15)", width=0.5)

    # 물리 엔진 설정
    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -80,
          "centralGravity": 0.01,
          "springLength": 120,
          "springConstant": 0.04,
          "damping": 0.9,
          "avoidOverlap": 0.3
        },
        "solver": "forceAtlas2Based",
        "stabilization": {
          "enabled": true,
          "iterations": 300
        }
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 100,
        "navigationButtons": true,
        "keyboard": true
      },
      "edges": {
        "arrows": { "to": { "enabled": true, "scaleFactor": 0.3 } },
        "smooth": { "type": "continuous" }
      }
    }
    """)

    net.save_graph(str(out_path))

    # HTML에 제목·범례 삽입
    html = out_path.read_text(encoding="utf-8")
    legend_html = """
    <div style="position:fixed;top:10px;left:10px;background:rgba(0,0,0,0.8);
         color:white;padding:15px;border-radius:8px;font-family:sans-serif;
         font-size:13px;z-index:1000;max-width:280px;">
      <h3 style="margin:0 0 8px 0;">🕸️ Owen WIKI Graph</h3>
      <p style="margin:0 0 5px 0;font-size:11px;opacity:0.8;">
        Nodes: {nodes} · Edges: {edges} · Communities: {comms}
      </p>
      <p style="margin:0;font-size:11px;opacity:0.6;">
        노드 크기 = 연결 수 · 색상 = 커뮤니티<br>
        마우스 호버 → 상세 정보 · 스크롤 → 줌
      </p>
    </div>
    """.format(
        nodes=analysis["nodes"],
        edges=analysis["edges"],
        comms=analysis["n_communities"],
    )
    html = html.replace("<body>", f"<body>{legend_html}")
    out_path.write_text(html, encoding="utf-8")


def write_report(analysis: dict, page_meta: dict, out_path: Path):
    """텍스트 보고서 생성."""
    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines.append(f"# WIKI Graph Report")
    lines.append(f"> Generated: {now}\n")
    lines.append("---\n")

    # 기본 통계
    lines.append("## 기본 통계\n")
    lines.append(f"| 항목 | 값 |")
    lines.append(f"|------|-----|")
    lines.append(f"| 노드 (페이지) | {analysis['nodes']} |")
    lines.append(f"| 엣지 (위키링크) | {analysis['edges']} |")
    lines.append(f"| 커뮤니티 (Louvain) | {analysis['n_communities']} |")
    lines.append(f"| 연결 컴포넌트 | {analysis['n_components']} |")
    lines.append(f"| 최대 컴포넌트 크기 | {analysis['largest_component']} |")
    lines.append(f"| 고아 노드 (degree=0) | {len(analysis['orphans'])} |")
    lines.append(f"| 인바운드 0 (위키 페이지) | {len(analysis['no_inbound'])} |")
    lines.append(f"| 커뮤니티 간 엣지 | {analysis['cross_community_edges']} |")
    lines.append("")

    # God Nodes (Top 20 by degree)
    lines.append("## God Nodes (연결 수 Top 20)\n")
    lines.append("| # | 페이지 | Degree | In | Out | 커뮤니티 | 카테고리 |")
    lines.append("|---|--------|--------|-----|-----|---------|---------|")
    G_degree_in = {n: analysis["in_degree_top"] for n in []}  # placeholder
    partition = analysis["partition"]
    for i, (node, deg) in enumerate(analysis["god_nodes"], 1):
        meta = page_meta.get(node, {})
        cat = meta.get("_category", "?")
        comm = partition.get(node, "?")
        in_d = next((d for n, d in analysis["in_degree_top"] if n == node), "?")
        out_d = deg - in_d if isinstance(in_d, int) else "?"
        lines.append(f"| {i} | `{node}` | {deg} | {in_d} | {out_d} | {comm} | {cat} |")
    lines.append("")

    # Betweenness Centrality Top 10
    lines.append("## Betweenness Centrality Top 10\n")
    lines.append("| # | 페이지 | Betweenness | 커뮤니티 |")
    lines.append("|---|--------|-------------|---------|")
    for i, (node, bc) in enumerate(analysis["betweenness_top"], 1):
        comm = partition.get(node, "?")
        lines.append(f"| {i} | `{node}` | {bc:.4f} | {comm} |")
    lines.append("")

    # 커뮤니티 상세
    lines.append("## 커뮤니티 상세\n")
    communities = analysis["communities"]
    for comm_id in sorted(communities.keys()):
        members = communities[comm_id]
        # 카테고리 분포
        cat_dist = Counter()
        for m in members:
            cat = page_meta.get(m, {}).get("_category", "?")
            cat_dist[cat] += 1
        cat_str = ", ".join(f"{c}:{n}" for c, n in cat_dist.most_common())
        hub = max(members, key=lambda n: partition.get(n, 0) if False else
                  sum(1 for _ in []))  # placeholder
        lines.append(f"### Community {comm_id} ({len(members)}개 노드)")
        lines.append(f"- 카테고리 분포: {cat_str}")
        # 상위 5개 노드
        member_sorted = sorted(members, key=lambda n: analysis["partition"].get(n, 0))
        sample = members[:10] if len(members) > 10 else members
        lines.append(f"- 주요 노드: {', '.join(f'`{n}`' for n in sample)}")
        if len(members) > 10:
            lines.append(f"- ... 외 {len(members) - 10}개")
        lines.append("")

    # 고아 노드
    if analysis["orphans"]:
        lines.append("## 고아 노드 (연결 없음)\n")
        for o in sorted(analysis["orphans"]):
            lines.append(f"- `{o}`")
        lines.append("")

    # 인바운드 없는 위키 페이지
    if analysis["no_inbound"]:
        lines.append("## 인바운드 링크 없는 위키 페이지\n")
        for n in sorted(analysis["no_inbound"]):
            meta = page_meta.get(n, {})
            cat = meta.get("_category", "?")
            lines.append(f"- `{n}` ({cat})")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Owen WIKI 위키링크 그래프 시각화")
    parser.add_argument("--wiki-dir", default="wiki", help="위키 폴더 경로 (기본: wiki)")
    parser.add_argument("--out-dir", default="graphify-out", help="출력 폴더 (기본: graphify-out)")
    args = parser.parse_args()

    # 경로 해석 (스크립트 위치 기준 → 프로젝트 루트)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    wiki_dir = Path(args.wiki_dir)
    if not wiki_dir.is_absolute():
        wiki_dir = project_root / wiki_dir

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = project_root / out_dir

    if not wiki_dir.exists():
        print(f"ERROR: wiki 폴더를 찾을 수 없습니다: {wiki_dir}")
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) 그래프 구축
    print(f"📂 wiki 폴더 스캔: {wiki_dir}")
    G, page_meta = build_graph(wiki_dir)
    print(f"   노드: {G.number_of_nodes()}, 엣지: {G.number_of_edges()}")

    # 2) 분석
    print("🔍 그래프 분석 (Louvain 커뮤니티 탐지)...")
    analysis = analyze_graph(G, page_meta)
    print(f"   커뮤니티: {analysis['n_communities']}, 컴포넌트: {analysis['n_components']}")
    print(f"   God nodes: {', '.join(n for n, _ in analysis['god_nodes'][:5])}")
    print(f"   고아 노드: {len(analysis['orphans'])}개")

    # 3) HTML 시각화
    html_path = out_dir / "graph.html"
    print(f"🕸️  인터랙티브 그래프 생성: {html_path}")
    build_html(G, analysis, page_meta, html_path)

    # 4) 텍스트 보고서
    report_path = out_dir / "GRAPH_REPORT.md"
    print(f"📝 보고서 생성: {report_path}")
    write_report(analysis, page_meta, report_path)

    # 5) JSON 그래프 (쿼리용)
    json_path = out_dir / "graph.json"
    print(f"💾 그래프 JSON 저장: {json_path}")
    data = nx.node_link_data(G)
    import json
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n✅ 완료! 출력 폴더: {out_dir}")
    print(f"   - graph.html   → 브라우저에서 열어 인터랙티브 탐색")
    print(f"   - GRAPH_REPORT.md → God nodes, 커뮤니티, 고아 노드 분석")
    print(f"   - graph.json   → 프로그래밍 방식 쿼리용")


if __name__ == "__main__":
    main()
