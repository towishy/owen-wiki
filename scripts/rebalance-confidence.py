#!/usr/bin/env python3
"""rebalance-confidence.py — 1차 소스 페이지의 confidence를 0.85+로 재평가

규칙 (AGENTS.md v1.4.0+ Confidence Scoring 가이드):
- type/mslearn 또는 type/ninja 태그 보유 → 0.85 (Microsoft 공식)
- type/webinar + prod/* (MS 제품) → 0.85
- sources에 Microsoft Learn URL 포함 → 0.90
- type/security-school + sources 5+ → 0.85
- 그 외는 변경하지 않음

기본값 (apply-default-confidence.py)으로 0.75를 받은 페이지 중 위 조건 충족 시 상향.
"""
from __future__ import annotations
import os, re, sys
from pathlib import Path

if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "wiki"

apply_changes = "--apply" in sys.argv


def parse_fm(text: str):
    if not text.startswith("---"): return None, None, text
    end = text.find("---", 3)
    if end == -1: return None, None, text
    return text[3:end], text[:end+3], text[end+3:]


def get_field(fm: str, key: str) -> str | None:
    m = re.search(rf"^{re.escape(key)}:\s*(.+?)$", fm, re.MULTILINE)
    return m.group(1).strip() if m else None


def get_tags(fm: str) -> list[str]:
    m = re.search(r"^tags:\s*\[(.+?)\]", fm, re.MULTILINE)
    if not m: return []
    return [t.strip().strip('"').strip("'") for t in m.group(1).split(",")]


def get_sources_count(fm: str) -> int:
    m = re.search(r"^sources:\s*\n((?:\s+-\s+.+\n?)+)", fm, re.MULTILINE)
    if not m:
        # inline
        m2 = re.search(r"^sources:\s*\[(.+?)\]", fm, re.MULTILINE)
        if m2: return len([x for x in m2.group(1).split(",") if x.strip()])
        return 0
    return len(re.findall(r"^\s+-\s+", m.group(1), re.MULTILINE))


def has_mslearn_url(fm: str) -> bool:
    return "learn.microsoft.com" in fm or "docs.microsoft.com" in fm


def evaluate(fm: str) -> float | None:
    tags = get_tags(fm)
    src_count = get_sources_count(fm)
    if has_mslearn_url(fm):
        return 0.90
    if "type/mslearn" in tags or "type/ninja" in tags:
        return 0.85
    if "type/security-school" in tags and src_count >= 5:
        return 0.85
    if "type/webinar" in tags and any(t.startswith("prod/") for t in tags):
        return 0.85
    return None


def update_confidence(fm: str, new_val: float) -> str:
    if "confidence:" in fm:
        return re.sub(r"^confidence:\s*[\d.]+", f"confidence: {new_val}", fm, flags=re.MULTILINE)
    return fm + f"\nconfidence: {new_val}"


def main() -> int:
    candidates = []
    for sub in ("entities", "concepts", "summaries", "synthesis", "comparisons"):
        for f in (WIKI / sub).glob("*.md"):
            if f.name == "_index.md": continue
            text = f.read_text(encoding="utf-8")
            fm_inner, fm_full, body = parse_fm(text)
            if not fm_inner: continue
            cur_str = get_field(fm_inner, "confidence")
            if not cur_str: continue
            try: cur = float(cur_str)
            except ValueError: continue
            new_val = evaluate(fm_inner)
            if new_val is None or new_val <= cur: continue
            candidates.append((f, cur, new_val, fm_inner, fm_full, body))

    print(f"=== Confidence Rebalance: {len(candidates)} candidates ===\n")
    for f, cur, nv, *_ in candidates[:20]:
        print(f"  {cur:.2f} -> {nv:.2f}  {f.relative_to(ROOT)}")
    if len(candidates) > 20:
        print(f"  ... +{len(candidates)-20} more")

    if not apply_changes:
        print("\n(dry-run) Run with --apply to update.")
        return 0

    for f, cur, nv, fm_inner, fm_full, body in candidates:
        new_fm = update_confidence(fm_inner, nv)
        f.write_text(f"---{new_fm}---{body}", encoding="utf-8")
    print(f"\nUpdated {len(candidates)} pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
