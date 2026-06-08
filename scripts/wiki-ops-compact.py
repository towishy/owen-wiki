#!/usr/bin/env python3
"""Create CCR-like compact reports for large wiki-ops outputs.

The script keeps source files unchanged and writes a compact Markdown/JSON sidecar
that an LLM can read first. Originals remain retrievable by path and SHA-256.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT_DIR = ROOT / "scripts" / "wiki-ops" / "compact"
DEFAULT_SOURCE_DIR = ROOT / "scripts" / "wiki-ops"

ERROR_RE = re.compile(r"error|exception|failed|failure|fatal|critical|warning|broken|orphan|stale|missing|invalid", re.I)
KEY_HINTS = (
    "score",
    "weight",
    "confidence",
    "count",
    "total",
    "updated",
    "generated_at",
    "status",
    "severity",
    "risk",
    "page",
    "path",
    "source",
    "target",
    "relation",
    "title",
    "slug",
    "name",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[Any]:
    records = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        records.append(json.loads(line))
    return records


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def scalar_preview(value: Any, limit: int = 160) -> str:
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    else:
        text = str(value)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        return text[: limit - 1] + "…"
    return text


def item_text(item: Any) -> str:
    return json.dumps(item, ensure_ascii=False, sort_keys=True) if isinstance(item, (dict, list)) else str(item)


def item_score(item: Any) -> float:
    text = item_text(item)
    score = 0.0
    if ERROR_RE.search(text):
        score += 1000.0
    if isinstance(item, dict):
        for key, value in item.items():
            key_lower = str(key).lower()
            if any(hint in key_lower for hint in KEY_HINTS):
                score += 2.0
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                score += min(abs(float(value)), 1000.0) / 100.0
            if ERROR_RE.search(str(value)):
                score += 100.0
    score += min(len(text), 2000) / 1000.0
    return score


def pick_representative(items: list[Any], limit: int) -> list[Any]:
    if limit <= 0 or len(items) <= limit:
        return items
    selected: list[tuple[int, Any]] = []
    seen: set[int] = set()

    def add(index: int) -> None:
        if 0 <= index < len(items) and index not in seen:
            selected.append((index, items[index]))
            seen.add(index)

    for index, item in enumerate(items):
        if ERROR_RE.search(item_text(item)):
            add(index)
            if len(selected) >= limit:
                return [item for _idx, item in sorted(selected)]

    boundary = max(1, min(3, limit // 4 or 1))
    for index in range(boundary):
        add(index)
    for index in range(len(items) - boundary, len(items)):
        add(index)

    ranked = sorted(((item_score(item), index) for index, item in enumerate(items) if index not in seen), reverse=True)
    for _score, index in ranked:
        add(index)
        if len(selected) >= limit:
            break
    return [item for _idx, item in sorted(selected)]


def common_fields(items: list[Any]) -> dict[str, Any]:
    dicts = [item for item in items if isinstance(item, dict)]
    if len(dicts) < 2:
        return {}
    keys = set(dicts[0])
    for item in dicts[1:]:
        keys &= set(item)
    common: dict[str, Any] = {}
    for key in sorted(keys):
        first = dicts[0][key]
        if all(item.get(key) == first for item in dicts[1:]):
            common[str(key)] = first
    return common


def summarize_records(records: list[Any], limit: int) -> dict[str, Any]:
    type_counts = Counter(type(item).__name__ for item in records)
    preserved = pick_representative(records, limit)
    error_count = sum(1 for item in records if ERROR_RE.search(item_text(item)))
    key_counts = Counter()
    for item in records:
        if isinstance(item, dict):
            key_counts.update(str(key) for key in item.keys())
    return {
        "kind": "records",
        "total_items": len(records),
        "preserved_items": len(preserved),
        "error_like_items": error_count,
        "type_counts": dict(type_counts.most_common()),
        "top_keys": dict(key_counts.most_common(20)),
        "common_fields": common_fields(records),
        "items": preserved,
    }


def find_large_arrays(value: Any, path: str = "$", min_items: int = 5) -> list[tuple[str, list[Any]]]:
    found: list[tuple[str, list[Any]]] = []
    if isinstance(value, list):
        if len(value) >= min_items:
            found.append((path, value))
        for index, item in enumerate(value[:50]):
            found.extend(find_large_arrays(item, f"{path}[{index}]", min_items=min_items))
    elif isinstance(value, dict):
        for key, child in value.items():
            found.extend(find_large_arrays(child, f"{path}.{key}", min_items=min_items))
    return found


def summarize_json(value: Any, limit: int) -> dict[str, Any]:
    if isinstance(value, list):
        return summarize_records(value, limit)
    if isinstance(value, dict):
        arrays = find_large_arrays(value)
        summary: dict[str, Any] = {
            "kind": "json_object",
            "top_level_keys": list(value.keys())[:40],
            "scalar_preview": {key: scalar_preview(val) for key, val in value.items() if not isinstance(val, (dict, list))},
            "arrays": [],
        }
        for array_path, items in sorted(arrays, key=lambda pair: len(pair[1]), reverse=True)[:8]:
            compact = summarize_records(items, limit)
            summary["arrays"].append({"path": array_path, **compact})
        return summary
    return {"kind": "scalar", "value": scalar_preview(value, 1000)}


def summarize_text(text: str, limit: int) -> dict[str, Any]:
    lines = text.splitlines()
    non_empty = [line for line in lines if line.strip()]
    error_lines = [(idx, line) for idx, line in enumerate(lines, 1) if ERROR_RE.search(line)]
    preserved: list[dict[str, Any]] = []
    seen: set[int] = set()

    def add(line_no: int, line: str) -> None:
        if line_no not in seen:
            preserved.append({"line": line_no, "text": line[:500]})
            seen.add(line_no)

    for line_no, line in error_lines[:limit]:
        add(line_no, line)
    for line_no in list(range(1, min(4, len(lines)) + 1)) + list(range(max(1, len(lines) - 2), len(lines) + 1)):
        if 1 <= line_no <= len(lines):
            add(line_no, lines[line_no - 1])
    if len(preserved) < limit:
        step = max(1, len(lines) // max(1, limit - len(preserved)))
        for idx in range(0, len(lines), step):
            add(idx + 1, lines[idx])
            if len(preserved) >= limit:
                break
    return {
        "kind": "text",
        "line_count": len(lines),
        "non_empty_lines": len(non_empty),
        "error_like_lines": len(error_lines),
        "preserved_lines": sorted(preserved, key=lambda item: item["line"]),
    }


def compact_path(path: Path, item_limit: int) -> dict[str, Any]:
    suffix = path.suffix.lower()
    source_hash = sha256_file(path)
    size_bytes = path.stat().st_size
    if suffix == ".json":
        summary = summarize_json(load_json(path), item_limit)
    elif suffix == ".jsonl":
        summary = summarize_records(load_jsonl(path), item_limit)
    else:
        summary = summarize_text(read_text(path), item_limit)
    return {
        "schema": "wiki-ops-compact.v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_path": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path),
        "source_sha256": source_hash,
        "source_size_bytes": size_bytes,
        "item_limit": item_limit,
        "retrieval": {
            "mode": "local-file",
            "path": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path),
            "sha256": source_hash,
        },
        "summary": summary,
    }


def md_table(rows: list[list[Any]]) -> list[str]:
    output = ["| " + " | ".join(str(cell) for cell in rows[0]) + " |"]
    output.append("|" + "|".join("---" for _ in rows[0]) + "|")
    for row in rows[1:]:
        output.append("| " + " | ".join(str(cell).replace("\n", " ") for cell in row) + " |")
    return output


def render_compact(compact: dict[str, Any]) -> str:
    source = compact["source_path"]
    summary = compact["summary"]
    lines = [
        f"# Wiki Ops Compact - {Path(source).name}",
        "",
        "## Retrieval",
        "",
        f"- source: `{source}`",
        f"- sha256: `{compact['source_sha256']}`",
        f"- bytes: `{compact['source_size_bytes']}`",
        "- rule: read this compact report first; retrieve the source path above when the task needs full detail.",
        "",
        "## Summary",
        "",
        f"- kind: `{summary.get('kind')}`",
    ]
    if summary.get("kind") == "records":
        lines.extend([
            f"- total_items: `{summary['total_items']}`",
            f"- preserved_items: `{summary['preserved_items']}`",
            f"- error_like_items: `{summary['error_like_items']}`",
            "",
            "### Top Keys",
            "",
        ])
        lines.extend(md_table([["Key", "Count"], *list(summary.get("top_keys", {}).items())[:12]]))
        lines.extend(["", "### Preserved Items", ""])
        for idx, item in enumerate(summary.get("items", []), 1):
            lines.append(f"```json\n{json.dumps(item, ensure_ascii=False, indent=2)}\n```")
            if idx >= compact["item_limit"]:
                break
    elif summary.get("kind") == "json_object":
        lines.append(f"- top_level_keys: `{', '.join(summary.get('top_level_keys', [])[:20])}`")
        if summary.get("scalar_preview"):
            lines.extend(["", "### Scalars", ""])
            lines.extend(md_table([["Key", "Preview"], *summary["scalar_preview"].items()]))
        for array in summary.get("arrays", []):
            lines.extend([
                "",
                f"### Array `{array['path']}`",
                "",
                f"- total_items: `{array['total_items']}`",
                f"- preserved_items: `{array['preserved_items']}`",
                f"- error_like_items: `{array['error_like_items']}`",
                "",
            ])
            for item in array.get("items", [])[: compact["item_limit"]]:
                lines.append(f"```json\n{json.dumps(item, ensure_ascii=False, indent=2)}\n```")
    elif summary.get("kind") == "text":
        lines.extend([
            f"- line_count: `{summary['line_count']}`",
            f"- non_empty_lines: `{summary['non_empty_lines']}`",
            f"- error_like_lines: `{summary['error_like_lines']}`",
            "",
            "### Preserved Lines",
            "",
        ])
        for item in summary.get("preserved_lines", []):
            lines.append(f"- L{item['line']}: {item['text']}")
    else:
        lines.append(f"- value: `{summary.get('value', '')}`")
    return "\n".join(lines) + "\n"


def discover_default_inputs() -> list[Path]:
    if not DEFAULT_SOURCE_DIR.exists():
        return []
    paths = []
    for pattern in ("*.json", "*.jsonl", "*.md", "*.log", "*.txt"):
        paths.extend(DEFAULT_SOURCE_DIR.glob(pattern))
    return sorted(path for path in paths if path.parent != DEFAULT_OUT_DIR and ".compact" not in path.name)


def write_index(out_dir: Path, compacts: list[dict[str, Any]]) -> None:
    rows = [["Source", "Kind", "Bytes", "Hash"]]
    for compact in compacts:
        rows.append([
            f"`{compact['source_path']}`",
            f"`{compact['summary'].get('kind')}`",
            compact["source_size_bytes"],
            f"`{compact['source_sha256'][:12]}`",
        ])
    lines = ["# Wiki Ops Compact Index", "", *md_table(rows), ""]
    (out_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")
    (out_dir / "index.json").write_text(json.dumps({"schema": "wiki-ops-compact-index.v1", "generated_at": datetime.now().isoformat(timespec="seconds"), "results": compacts}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="wiki-ops JSON/JSONL/Markdown/log files. Defaults to scripts/wiki-ops/*.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Output directory for compact sidecars")
    parser.add_argument("--item-limit", type=int, default=12, help="Maximum preserved records/lines per section")
    parser.add_argument("--min-bytes", type=int, default=0, help="Skip files below this size")
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    inputs = args.paths or discover_default_inputs()
    paths = [path for path in inputs if path.exists() and path.is_file() and path.stat().st_size >= args.min_bytes]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    compacts = []
    for path in paths:
        compact = compact_path(path.resolve(), args.item_limit)
        compacts.append(compact)
        stem = re.sub(r"[^A-Za-z0-9._-]", "-", path.stem)[:90]
        (args.out_dir / f"{stem}.compact.json").write_text(json.dumps(compact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (args.out_dir / f"{stem}.compact.md").write_text(render_compact(compact), encoding="utf-8")
    write_index(args.out_dir, compacts)
    if not args.quiet:
        print(f"Wrote {len(compacts)} compact report(s) to {args.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
