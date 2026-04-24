"""Fix corrupt source paths (backslash + mojibaked Korean) in 4 cluster hubs.
Strategy: walk raw/ filesystem and re-derive sources by filename pattern matching."""
import os
import re
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"

# Each hub: (filename, list of (root_subdir, filename_substring_filter))
HUBS = {
    "secmde-tactical-scenarios-hub.md": [
        ("extracted", "Tactical Scenarios Guide"),
    ],
    "mdc-workshop-content-hub.md": [
        ("extracted/microsoft-documents/workshop - defender for cloud", None),
        ("extracted/microsoft-documents/VBD - Accelerate Cloud Security", None),
        ("extracted/microsoft-documents/VBD - CSPM and WP - Solution Optimization", None),
        ("extracted/microsoft-documents/VBD-Accelerate Cloud Security", None),
        ("extracted/onsite-reports/KBHC - Workshop - Defender for Cloud", None),
        ("extracted/onsite-reports/KB증권-MDC-교육", None),
        ("extracted/onsite-reports/캐롯손해보험-MDC", None),
    ],
    "fy26-techconnect-sessions-hub.md": [
        ("extracted/fy26-readiness", "techconnect"),
        ("extracted/fy26-readiness", "tech connect"),
        ("extracted/microsoft-documents/FY25-Readiness/FY25-Tech Connect", None),
        ("extracted/readiness-archives", "TechConnect"),
    ],
    "sentinel-korea-customer-content-hub.md": [
        ("extracted/microsoft-documents/MS korea Nexus", "sentinel"),
        ("extracted/microsoft-documents/MS korea Nexus", "센티넬"),
        ("extracted/onsite-reports", "sentinel"),
        ("extracted/onsite-reports", "센티넬"),
        ("extracted/microsoft-documents/Sentinel", None),
        ("extracted/microsoft-documents/Workshop-Sentinel", None),
        ("extracted/microsoft-documents/Workshop-Sentinel Fundermental", None),
    ],
}

def collect(root_subdir, name_filter):
    base = RAW / root_subdir
    if not base.exists():
        return []
    out = []
    for p in base.rglob("*.md"):
        if name_filter and name_filter.lower() not in p.name.lower() and name_filter.lower() not in str(p).lower():
            continue
        rel = p.relative_to(ROOT).as_posix()
        out.append(rel)
    return out

for hub_fname, patterns in HUBS.items():
    hub_path = ROOT / "wiki" / "summaries" / hub_fname
    if not hub_path.exists():
        print(f"[skip] {hub_fname} not found")
        continue
    text = hub_path.read_text(encoding="utf-8")

    # collect new paths
    found = set()
    for sub, flt in patterns:
        for p in collect(sub, flt):
            found.add(p)
    paths = sorted(found)
    print(f"{hub_fname}: {len(paths)} sources from filesystem")

    # Replace the sources block
    src_yaml = "\n".join(f'  - "{p}"' for p in paths)
    new_text = re.sub(
        r"(?ms)^sources:\n(?:  - \"[^\"]*\"\n)+",
        f"sources:\n{src_yaml}\n",
        text,
        count=1,
    )
    if new_text == text:
        print(f"  WARN: source block not replaced in {hub_fname}")
        continue
    # update the count mention in body if present
    new_text = re.sub(r"(\d+)개 소스 파일이 sources 필드에 등록", f"{len(paths)}개 소스 파일이 sources 필드에 등록", new_text)
    new_text = re.sub(r"updated: \d{4}-\d{2}-\d{2}", "updated: 2026-04-24", new_text)
    hub_path.write_text(new_text, encoding="utf-8")
    print(f"  wrote {hub_fname}")
