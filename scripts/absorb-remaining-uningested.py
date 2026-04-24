"""Absorb remaining uningested candidates into existing hubs by best-fit routing.

Strategy:
1. Run find-uningested-raw to get all remaining candidate paths.
2. Route each path to the best-fit existing hub by prefix/keyword rules.
3. APPEND new paths to each hub's sources YAML block (union, sorted, deduped).
4. Update hub's body source-count mention.
"""
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
os.environ["PYTHONIOENCODING"] = "utf-8"

# Run scanner
print("[1/3] Scanning uningested...")
res = subprocess.run(
    [sys.executable, "scripts/find-uningested-raw.py", "--top", "10000"],
    capture_output=True, text=True, encoding="utf-8",
)
row_re = re.compile(r"^\|\s*\d+\s*\|\s*-?\d+\s*\|\s*\S+\s*\|\s*`(raw/[^`]+)`")
candidates = [m.group(1) for line in res.stdout.splitlines() if (m := row_re.match(line))]
print(f"  parsed {len(candidates)} candidates")

# Routing rules — order matters (first match wins)
ROUTES = [
    # Hyundai (MS Korea Nexus 04. Hyundai)
    ("ms-korea-microsoft-documents-hub.md",
     lambda p: "/MS korea Nexus/" in p),
    # SecMDE Tactical Scenarios (already a hub but add stragglers)
    ("secmde-tactical-scenarios-hub.md",
     lambda p: "Tactical Scenarios Guide" in p),
    # MDC / VBD CSPM / Defender for Cloud
    ("mdc-workshop-content-hub.md",
     lambda p: any(k in p for k in (
         "VBD-Accelerate Cloud Security",
         "VBD - Accelerate Cloud Security",
         "VBD - CSPM",
         "/Defender for Cloud/",
         "/Defender for Cloud-",
         "/대림-MDC-CSPM/",
         "/KBHC - Workshop - Defender for Cloud/",
         "/KB증권-MDC",
         "/캐롯손해보험-MDC",
         "/MDC_",
         "/MDFC_",
         "MDC CSPM",
         "MDEASM",
         "Defender for Cloud Container",
         "Defender for Cloud-CWPP",
     ))),
    # Sentinel / SOC Optimization
    ("sentinel-korea-customer-content-hub.md",
     lambda p: any(k in p for k in (
         "/Sentinel/",
         "/Sentinel ",
         "Microsoft Sentinel",
         "VBD-SOC Optimization",
         "VBD-Sentinel",
         "센티넬",
         "SecSent",
         "SOSent",
         "SecSentAdv",
         "OSOSent",
         "MS Sentinel",
         "SIEM",
         "Unified SOC Platform",
     ))),
    # FY26 TechConnect
    ("fy26-techconnect-sessions-hub.md",
     lambda p: "/fy26-readiness/" in p.lower() or "techconnect" in p.lower() or "tech connect" in p.lower()),
    # FY24/FY23 Readiness Archives
    ("readiness-archives-hub.md",
     lambda p: "/readiness-archives/" in p),
    # FY26 readiness extras (anything fy26 not techconnect)
    ("fy26-readiness-extras-hub.md",
     lambda p: "/fy26-readiness/" in p.lower()),
    # Onsite reports (catch-all for onsite-reports/)
    ("onsite-reports-content-hub.md",
     lambda p: "/onsite-reports/" in p),
    # MS Korea microsoft-documents (catch-all)
    ("ms-korea-microsoft-documents-hub.md",
     lambda p: "/extracted/microsoft-documents/" in p),
]

routes_count = defaultdict(list)
unrouted = []
for c in candidates:
    matched = False
    for hub_fname, predicate in ROUTES:
        if predicate(c):
            routes_count[hub_fname].append(c)
            matched = True
            break
    if not matched:
        unrouted.append(c)

print(f"\n[2/3] Routing summary:")
for hub, paths in sorted(routes_count.items(), key=lambda kv: -len(kv[1])):
    print(f"  {hub}: +{len(paths)}")
print(f"  UNROUTED: {len(unrouted)}")
if unrouted[:10]:
    print("  Examples:")
    for u in unrouted[:10]:
        print(f"    {u}")

# Apply: APPEND new paths to each hub's sources block
print(f"\n[3/3] Updating hubs...")
SUMMARIES = ROOT / "wiki" / "summaries"
src_block_re = re.compile(r"(?ms)^sources:\n((?:  - \"[^\"]*\"\n)+)")

for hub_fname, new_paths in routes_count.items():
    hub_path = SUMMARIES / hub_fname
    if not hub_path.exists():
        print(f"  SKIP (missing): {hub_fname}")
        continue
    text = hub_path.read_text(encoding="utf-8")
    m = src_block_re.search(text)
    if not m:
        print(f"  SKIP (no sources block): {hub_fname}")
        continue
    existing = set(re.findall(r'- "(raw/[^"]+)"', m.group(1)))
    merged = sorted(existing | set(new_paths))
    added = len(merged) - len(existing)
    new_block = "sources:\n" + "\n".join(f'  - "{p}"' for p in merged) + "\n"
    new_text = text[: m.start()] + new_block + text[m.end():]
    # Update count mention in body if present
    new_text = re.sub(
        r"\d+개 소스 파일이 sources 필드에 등록",
        f"{len(merged)}개 소스 파일이 sources 필드에 등록",
        new_text,
    )
    new_text = re.sub(r"updated: \d{4}-\d{2}-\d{2}", "updated: 2026-04-24", new_text)
    hub_path.write_text(new_text, encoding="utf-8")
    print(f"  {hub_fname}: {len(existing)} → {len(merged)} (+{added})")
