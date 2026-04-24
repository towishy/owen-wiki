#!/usr/bin/env python3
"""
append-ontology.py — 트리플렛 YAML을 적절한 *-ontology.md 파일에 dedupe 후 APPEND

입력 형식 (auto-extract-triplets.py 출력 또는 수동):
```yaml
ENTITIES:
  - name: "..."
    type: ...
RELATIONS:
  - source: "..."
    relation: ...
    target: "..."
    evidence: "..."
```

라우팅 규칙:
- source/target이 entities/ 페이지 → entities-ontology.md
- source/target이 concepts/ 페이지 → concepts-ontology.md
- source/target이 summaries/ 페이지 → summaries-ontology.md
- source/target이 synthesis/ 페이지 → synthesis-ontology.md
- 카테고리 횡단 → full-wiki-ontology.md

사용법:
  python scripts/append-ontology.py triplets.yaml
  cat triplets.yaml | python scripts/append-ontology.py -
"""
from __future__ import annotations
import os, sys, re, yaml
from pathlib import Path

if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "wiki"
ONTO = WIKI / "ontology"


def page_category() -> dict[str, str]:
    cat = {}
    for sub in ("entities", "concepts", "summaries", "synthesis", "comparisons"):
        d = WIKI / sub
        if not d.exists(): continue
        for f in d.glob("*.md"):
            if f.name == "_index.md": continue
            cat[f.stem] = sub
    return cat


def parse_yaml_block(text: str) -> dict:
    # 입력에서 ```yaml ... ``` 블록 추출 또는 raw YAML 파싱
    m = re.search(r"```yaml\n(.*?)\n```", text, re.DOTALL)
    if m: text = m.group(1)
    try:
        return yaml.safe_load(text) or {}
    except Exception as e:
        print(f"YAML parse error: {e}", file=sys.stderr)
        return {}


def route_relation(src: str, tgt: str, cats: dict[str, str]) -> str:
    sc = cats.get(src)
    tc = cats.get(tgt)
    if not sc or not tc:
        return "full-wiki-ontology"
    if sc == tc:
        return f"{sc}-ontology"
    return "full-wiki-ontology"


def existing_relations(path: Path) -> set[tuple[str, str, str]]:
    if not path.exists(): return set()
    text = path.read_text(encoding="utf-8")
    pat = re.compile(r"\[\[([^\]]+)\]\]\s+\[([^\]]+)\]\s+\[\[([^\]]+)\]\]")
    return {(m.group(1).strip(), m.group(2).strip(), m.group(3).strip())
            for m in pat.finditer(text)}


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__); return 1
    src = sys.argv[1]
    text = sys.stdin.read() if src == "-" else Path(src).read_text(encoding="utf-8")
    data = parse_yaml_block(text)
    relations = data.get("RELATIONS", [])
    if not relations:
        print("No RELATIONS found"); return 1

    cats = page_category()
    routed: dict[str, list[tuple[str, str, str, str]]] = {}
    for r in relations:
        s = (r.get("source") or "").strip()
        rel = (r.get("relation") or "").strip()
        t = (r.get("target") or "").strip()
        ev = (r.get("evidence") or "").strip()
        if not (s and rel and t): continue
        target_file = route_relation(s, t, cats)
        routed.setdefault(target_file, []).append((s, rel, t, ev))

    total_added = 0
    for fname, items in routed.items():
        path = ONTO / f"{fname}.md"
        existing = existing_relations(path)
        new = [it for it in items if (it[0], it[1], it[2]) not in existing]
        if not new:
            print(f"  {fname}: 0 new (all dupes)")
            continue
        block = ["", f"<!-- AUTO-APPENDED {len(new)} relations -->"]
        for s, rel, t, ev in new:
            line = f"- [[{s}]] [{rel}] [[{t}]]"
            if ev: line += f" — _{ev}_"
            block.append(line)
        block.append("")
        with path.open("a", encoding="utf-8") as f:
            f.write("\n".join(block))
        print(f"  {fname}: +{len(new)} relations")
        total_added += len(new)
    print(f"\nTotal appended: {total_added}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
