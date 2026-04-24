#!/usr/bin/env python3
"""
find-uningested-raw.py
─────────────────────────────────────────────────────────────
raw/ 폴더에서 wiki/ 의 어떤 페이지에서도 sources 필드 또는 본문에서
참조하지 않은 파일을 찾아 우선순위와 함께 보고한다.

산출:
  - 콘솔 요약
  - outputs/reports/uningested-raw-YYYYMMDD.md (옵션)

스코프:
  - raw/articles/*.md (1차 후보, 인제스트 가장 빠름)
  - raw/extracted/**/*.md (PDF/PPTX 추출 결과)
  - raw/notes/**/*.md
  - 심볼릭 링크(obsidian, security-onsite-reports, security-microsoft-documents)는
    --include-symlinks 옵션 줄 때만 스캔 (대량 → 전용 모드)

우선순위 점수 (higher = better candidate):
  +5 : raw/articles/ 직속 (가장 가벼운 인제스트)
  +3 : 파일 크기 1KB ~ 200KB 범위 (적정)
  +2 : 파일명에 prod/topic 키워드 포함 (mde/sentinel/entra/gsa/purview/intune/copilot/zero-trust 등)
  +1 : 최근 90일 이내 수정
  -3 : 50KB 미만 (스텁 가능성)
  -2 : 500KB 초과 (분할 필요)

사용:
  python scripts/find-uningested-raw.py                 # 콘솔 요약 (기본 스코프)
  python scripts/find-uningested-raw.py --report        # outputs/reports/에 리포트 저장
  python scripts/find-uningested-raw.py --top 30        # 상위 N개 표시
  python scripts/find-uningested-raw.py --include-symlinks  # symlink 폴더도 스캔
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Iterable

# Windows 콘솔 UTF-8 강제
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
RAW = ROOT / "raw"
OUTPUTS = ROOT / "outputs" / "reports"

KEYWORDS = [
    "mde", "sentinel", "entra", "gsa", "purview", "intune", "copilot",
    "defender", "zero-trust", "kql", "soar", "siem", "edr", "xdr",
    "cnapp", "casb", "dlp", "mfa", "conditional-access", "ca-policy",
    "compliance", "ai-security", "ninja", "msem", "mdvm", "mdca", "mdo",
]

SCOPE_DIRS = ["articles", "extracted", "notes"]


def _norm(s: str) -> str:
    """NFC normalize + lowercase + backslash→slash."""
    return unicodedata.normalize("NFC", s.replace("\\", "/").lower())


def collect_wiki_references() -> set[str]:
    """wiki/ 안의 모든 페이지에서 raw/ 경로 참조를 추출."""
    refs: set[str] = set()
    if not WIKI.exists():
        return refs
    # 공백·한글·괄호·대괄호·작은따옴표 포함 파일명 지원. 닫는 큰따옴표·꺾쇠·줄끝에서 멈춤
    pat = re.compile(r"raw/[^\"`<>\n]+")
    for md in WIKI.rglob("*.md"):
        try:
            text = md.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in pat.finditer(text):
            path_part = m.group(0).rstrip(" \t.,;:)]")
            # markdown 링크 ](...) 닫기 + alias |
            path_part = path_part.split("|")[0].strip()
            refs.add(_norm(path_part))
    return refs


def is_referenced(rel_path: str, refs: set[str]) -> bool:
    rel = _norm(rel_path)
    if rel in refs:
        return True
    name = rel.rsplit("/", 1)[-1]
    # 정확한 파일명 일치 (확장자 포함)
    if any(name in r for r in refs):
        return True
    # 확장자 무시 매칭 — extracted/ 의 .md 가 원본 .pdf/.pptx/.docx/.xlsx 로 참조된 경우
    stem = name.rsplit(".", 1)[0]
    for r in refs:
        rname = r.rsplit("/", 1)[-1]
        rstem = rname.rsplit(".", 1)[0]
        if stem and stem == rstem:
            return True
    return False


def score_candidate(path: Path, root_for_rel: Path) -> tuple[int, list[str]]:
    score = 0
    notes: list[str] = []
    rel = path.relative_to(root_for_rel).as_posix().lower()

    if rel.startswith("raw/articles/"):
        score += 5
        notes.append("articles")

    try:
        size = path.stat().st_size
    except OSError:
        return -100, ["stat-fail"]

    if 1024 <= size <= 200_000:
        score += 3
    elif size < 50_000:
        score -= 3
        notes.append("small")
    elif size > 500_000:
        score -= 2
        notes.append("large")

    name = path.name.lower()
    matched = [k for k in KEYWORDS if k in name]
    if matched:
        score += 2
        notes.append("kw:" + ",".join(matched[:3]))

    try:
        mtime = dt.datetime.fromtimestamp(path.stat().st_mtime)
        if (dt.datetime.now() - mtime).days <= 90:
            score += 1
            notes.append("recent")
    except OSError:
        pass

    return score, notes


def iter_raw_files(include_symlinks: bool) -> Iterable[Path]:
    for sub in SCOPE_DIRS:
        d = RAW / sub
        if not d.exists():
            continue
        if d.is_symlink() and not include_symlinks:
            continue
        for p in d.rglob("*.md"):
            yield p
    if include_symlinks:
        for sub in ("obsidian", "security-onsite-reports", "security-microsoft-documents"):
            d = RAW / sub
            if not d.exists():
                continue
            for p in d.rglob("*.md"):
                yield p


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB"):
        if n < 1024:
            return f"{n:.0f}{unit}"
        n /= 1024
    return f"{n:.1f}GB"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=20, help="콘솔에 표시할 상위 N개 (기본 20)")
    ap.add_argument("--report", action="store_true", help="outputs/reports/ 에 마크다운 저장")
    ap.add_argument("--include-symlinks", action="store_true", help="심볼릭 링크 폴더도 스캔")
    args = ap.parse_args()

    refs = collect_wiki_references()
    print(f"[scan] wiki/ 페이지가 참조하는 raw/ 경로 {len(refs)}개 발견", file=sys.stderr)

    candidates: list[tuple[int, Path, int, list[str]]] = []
    total = 0
    skipped_referenced = 0
    for p in iter_raw_files(args.include_symlinks):
        total += 1
        rel = p.relative_to(ROOT).as_posix()
        if is_referenced(rel, refs):
            skipped_referenced += 1
            continue
        s, notes = score_candidate(p, ROOT)
        try:
            size = p.stat().st_size
        except OSError:
            continue
        candidates.append((s, p, size, notes))

    candidates.sort(key=lambda x: (-x[0], -x[2]))

    print()
    print(f"## 스캔 결과")
    print(f"- 스캔 파일: {total}")
    print(f"- 이미 참조됨: {skipped_referenced}")
    print(f"- 미인제스트 후보: {len(candidates)}")
    print()

    headers = ["순위", "점수", "크기", "경로", "키워드"]
    print(f"## 상위 {args.top}개 후보")
    print()
    print("| " + " | ".join(headers) + " |")
    print("|" + "|".join(["---"] * len(headers)) + "|")
    for i, (s, p, sz, notes) in enumerate(candidates[: args.top], 1):
        rel = p.relative_to(ROOT).as_posix()
        print(f"| {i} | {s} | {human_size(sz)} | `{rel}` | {', '.join(notes)} |")

    if args.report:
        OUTPUTS.mkdir(parents=True, exist_ok=True)
        today = dt.date.today().isoformat().replace("-", "")
        out = OUTPUTS / f"uningested-raw-{today}.md"
        with out.open("w", encoding="utf-8") as f:
            f.write(f"---\n")
            f.write(f"title: \"미인제스트 raw/ 후보 리포트\"\n")
            f.write(f"type: report\n")
            f.write(f"created: {dt.date.today().isoformat()}\n")
            f.write(f"updated: {dt.date.today().isoformat()}\n")
            f.write(f"---\n\n")
            f.write(f"# 미인제스트 raw/ 후보 리포트\n\n")
            f.write(f"- 스캔 파일: **{total}**\n")
            f.write(f"- 이미 참조됨: {skipped_referenced}\n")
            f.write(f"- 미인제스트 후보: **{len(candidates)}**\n")
            f.write(f"- 변환율: {(skipped_referenced / total * 100) if total else 0:.1f}%\n\n")
            f.write(f"## 전체 후보 (점수 내림차순)\n\n")
            f.write("| 순위 | 점수 | 크기 | 경로 | 키워드/메모 |\n")
            f.write("|---|---:|---:|---|---|\n")
            for i, (s, p, sz, notes) in enumerate(candidates, 1):
                rel = p.relative_to(ROOT).as_posix()
                f.write(f"| {i} | {s} | {human_size(sz)} | `{rel}` | {', '.join(notes)} |\n")
        print(f"\n[saved] {out.relative_to(ROOT).as_posix()}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
