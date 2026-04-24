#!/usr/bin/env python3
"""
gen-hub-category-index.py — 자동 클러스터 허브 본문에 카테고리별 sources 인덱스 생성

각 hub 페이지의 sources 목록을 1단계 경로(서브폴더)로 그룹화하여
"## 카테고리별 자료 (자동 생성)" 섹션을 본문 끝에 ADD하거나 REPLACE한다.

마커: `<!-- AUTO-CATEGORY-INDEX:START -->` ~ `<!-- AUTO-CATEGORY-INDEX:END -->`
"""
from __future__ import annotations
import os, re, sys, yaml
from pathlib import Path
from collections import defaultdict

if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
SUMMARIES = ROOT / "wiki" / "summaries"

START = "<!-- AUTO-CATEGORY-INDEX:START -->"
END = "<!-- AUTO-CATEGORY-INDEX:END -->"

HUB_PATTERNS = [
    re.compile(r"auto-hub-.*\.md$"),
    re.compile(r".*-content-hub\.md$"),
    re.compile(r".*-archives-hub\.md$"),
    re.compile(r".*-microsoft-documents-hub\.md$"),
    re.compile(r".*-sessions-hub\.md$"),
    re.compile(r".*-extras-hub\.md$"),
    re.compile(r".*-scenarios-hub\.md$"),
]


def is_hub(name: str) -> bool:
    return any(p.match(name) for p in HUB_PATTERNS)


def parse_frontmatter(text: str):
    if not text.startswith("---"):
        return None, text
    end = text.find("---", 3)
    if end == -1:
        return None, text
    try:
        fm = yaml.safe_load(text[3:end])
    except Exception:
        return None, text
    return fm, text[end + 3:]


def category_key(src: str) -> str:
    # raw/extracted/onsite-reports/Defender For Cloud-이베이-교육/foo.md → "Defender For Cloud-이베이-교육"
    parts = src.split("/")
    if len(parts) >= 4 and parts[0] == "raw":
        return parts[3] if len(parts) > 4 else parts[2]
    if len(parts) >= 3:
        return parts[2]
    return parts[1] if len(parts) > 1 else "기타"


def build_index_block(sources: list[str]) -> str:
    if not sources or len(sources) < 5:
        return ""
    groups: dict[str, list[str]] = defaultdict(list)
    for s in sources:
        groups[category_key(s)].append(s)
    if len(groups) < 2:
        return ""
    lines = [START, "", "## 카테고리별 자료 (자동 생성)", "",
             f"> 총 {len(sources)} 파일 / {len(groups)} 카테고리 — `scripts/gen-hub-category-index.py`로 자동 생성", ""]
    for cat in sorted(groups, key=lambda k: (-len(groups[k]), k)):
        files = groups[cat]
        lines.append(f"### {cat} ({len(files)})")
        lines.append("")
        for f in sorted(files)[:20]:
            name = Path(f).stem
            lines.append(f"- `{name}` — `{f}`")
        if len(files) > 20:
            lines.append(f"- … 외 {len(files) - 20}개 (sources 전체 목록 참조)")
        lines.append("")
    lines.append(END)
    return "\n".join(lines)


def update_hub(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    if not fm or "sources" not in fm:
        return False
    sources = fm.get("sources") or []
    block = build_index_block(sources)
    if not block:
        return False
    # remove existing block
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    new_body = pattern.sub("", body).rstrip() + "\n\n" + block + "\n"
    new_text = text[:text.find("---", 3) + 3] + new_body
    if new_text == text:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def main() -> int:
    updated = 0
    skipped = 0
    for f in sorted(SUMMARIES.glob("*.md")):
        if not is_hub(f.name):
            continue
        if update_hub(f):
            print(f"OK   {f.name}")
            updated += 1
        else:
            print(f"SKIP {f.name}")
            skipped += 1
    print(f"\nUpdated: {updated} / Skipped: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
