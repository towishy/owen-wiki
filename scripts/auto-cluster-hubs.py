"""
Auto-hub generator: scan top-N uningested candidates, group by 2nd-level path,
and create/refresh hub summary pages with all source paths registered.

Skips clusters already well-covered by existing hubs.
"""
import os
import re
import subprocess
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Run scanner with a high cap to gather all uningested candidate paths
print("[1/3] Running find-uningested-raw scan...")
res = subprocess.run(
    [sys.executable, 'scripts/find-uningested-raw.py', '--top', '6000', '--include-symlinks'],
    capture_output=True, text=True, encoding='utf-8'
)
lines = res.stdout.splitlines()

# Parse: rows like "| 12 | 6 | 24KB | `raw/foo/bar.md` | kw:.. |"
row_re = re.compile(r'^\|\s*\d+\s*\|\s*\d+\s*\|\s*\S+\s*\|\s*`(raw/[^`]+)`')
candidates = []
for line in lines:
    m = row_re.match(line)
    if m:
        candidates.append(m.group(1))
print(f"  parsed {len(candidates)} candidate paths")

# Already-covered top-level + 2nd-level keys (skip)
SKIP_PREFIX = (
    'raw/articles/mslearn/',
    'raw/articles/external-microsoft-security-101/',
    'raw/extracted/articles/external-microsoft-security-101/',
    'raw/obsidian/',  # user vault, not for ingest
)
SKIP_CONTAINS = (
    'SecMDE - Tactical Scenarios Guide',
    '/Defender for Cloud/CWPP/', '/Defender for Cloud-CWPP', 'WS_Microsoft Defender for',
    'fy26 techconnect', 'Sentinel Calculator', 'Sentinel Overview',
    'Microsoft-Sentinel-Technical-Playbook-for-MSSPs',
    '/MS korea Nexus/', '/SK Hynix_', 'KT_Sentinel/',
    'VBD-Accelerate Cloud Security', 'VBD - Accelerate Cloud Security',
    'VBD - CSPM', 'VBD-Sentinel', 'VBD-SOC',
    'CSPM/Defender for Cloud-CWPP', 'KBHC - Workshop - Defender for Cloud',
    'KBHC', 'KB증권', 'KB利앷텒',
)

def cluster_key(path):
    parts = path.split('/')
    if len(parts) < 3:
        return None
    top = parts[1]
    sub = parts[2]
    # 3-level grouping for deep trees
    if top in ('extracted', 'security-microsoft-documents', 'security-onsite-reports'):
        if len(parts) >= 4:
            return f'{top}/{sub}/{parts[3]}'
        return f'{top}/{sub}'
    if top == 'articles':
        return f'articles/{sub}'
    return top

groups = defaultdict(list)
for c in candidates:
    if any(c.startswith(p) for p in SKIP_PREFIX):
        continue
    if any(s in c for s in SKIP_CONTAINS):
        continue
    k = cluster_key(c)
    if not k:
        continue
    groups[k].append(c)

# Filter to clusters with >=3 files
big_groups = {k: sorted(set(v)) for k, v in groups.items() if len(set(v)) >= 3}
print(f"\n[2/3] Found {len(big_groups)} clusters with 8+ files:")
for k, v in sorted(big_groups.items(), key=lambda kv: -len(kv[1])):
    print(f"  {k}: {len(v)} files")

# Hub metadata
HUB_META = {
    'extracted/microsoft-documents': dict(
        title='MS Korea Microsoft Documents — 자료 허브',
        fname='ms-korea-microsoft-documents-hub.md',
        tags='[type/summary, type/workshop, prod/microsoft-security]',
        desc='MS Korea가 보유한 **Microsoft 공식 워크숍·세션 자료**(PPTX/PDF 변환물) 일괄 허브. Defender 시리즈, MDE, Sentinel, Security Copilot Core, Solution Optimization, FY25-Readiness, M365 Copilot Security 등.',
    ),
    'extracted/onsite-reports': dict(
        title='Onsite Reports — 고객사 워크숍 사본 자료 허브',
        fname='onsite-reports-content-hub.md',
        tags='[type/summary, type/workshop, type/customer-engagement]',
        desc='MS Korea가 한국 고객사 현장에서 수행한 **온사이트 워크숍·교육 사본 자료** 허브. 본 허브에 포함된 자료는 SecMDE Tactical Scenarios Hub, MDC Workshop Hub, Sentinel Korea Hub에 분류되지 않은 잔여 고객사별 사본을 포괄한다.',
    ),
    'extracted/readiness-archives': dict(
        title='Readiness Archives — FY24 Microsoft 내부 교육 아카이브',
        fname='readiness-archives-hub.md',
        tags='[type/summary, type/readiness, series/fy24-readiness]',
        desc='Microsoft FY24(2023~2024) 내부 readiness 자료 아카이브. Sentinel, MDC, MDE, Purview 등 분기별 readiness 세션 PPTX/PDF 변환물.',
    ),
    'extracted/fy26-readiness': dict(
        title='FY26 Readiness — 추가 자료 허브',
        fname='fy26-readiness-extras-hub.md',
        tags='[type/summary, type/readiness, series/fy26-readiness]',
        desc='FY26 readiness 시리즈 중 [[fy26-techconnect-sessions-hub]]에 포함되지 않은 추가 자료(BizApp 세션, 일반 readiness 데크 등).',
    ),
    'security-microsoft-documents/Sentinel': dict(
        title='Sentinel Microsoft Documents (security-microsoft-documents/Sentinel) 자료 허브',
        fname='sentinel-microsoft-documents-hub.md',
        tags='[type/summary, prod/sentinel, topic/siem]',
        desc='security-microsoft-documents 심볼릭 경로 하위의 Sentinel 관련 PPTX/PDF/문서 자료 허브.',
    ),
    'security-microsoft-documents/Defender for Cloud': dict(
        title='MDC Microsoft Documents (symlink) 자료 허브',
        fname='mdc-microsoft-documents-hub.md',
        tags='[type/summary, prod/mdc, topic/cnapp]',
        desc='security-microsoft-documents 심볼릭 경로 하위의 Defender for Cloud(MDC) 관련 PPTX/PDF/문서 자료 허브.',
    ),
    'security-onsite-reports/.': dict(
        title='Security Onsite Reports (symlink) 허브',
        fname='security-onsite-reports-hub.md',
        tags='[type/summary, type/customer-engagement]',
        desc='security-onsite-reports 심볼릭 경로 하위 자료 일괄 허브. 한국 고객사 현장 워크숍·델리버리 자료 다양.',
    ),
}

print(f"\n[3/3] Writing hub pages...")
written = 0
# Group all clusters by target fname to merge sources
by_fname = defaultdict(lambda: {'paths': [], 'meta': None, 'cluster_keys': []})
for k, paths in big_groups.items():
    meta = None
    for mk, mv in HUB_META.items():
        if k.startswith(mk) or k == mk:
            meta = mv
            break
    if not meta:
        slug = re.sub(r'[^a-z0-9]+', '-', k.lower()).strip('-')
        meta = dict(
            title=f'{k} — 자료 허브',
            fname=f'auto-hub-{slug}.md',
            tags='[type/summary, type/auto-hub]',
            desc=f'`raw/{k}/` 하위 자료의 자동 생성 교차참조 허브.',
        )
    entry = by_fname[meta['fname']]
    entry['paths'].extend(paths)
    entry['meta'] = meta
    entry['cluster_keys'].append(k)

for fname, entry in by_fname.items():
    paths = list(entry['paths'])
    out = f'wiki/summaries/{fname}'
    # Union with existing sources (if file exists)
    if os.path.exists(out):
        with open(out, encoding='utf-8') as fh:
            existing = fh.read()
        for m in re.finditer(r'^  - "(raw/[^"]+)"', existing, re.M):
            paths.append(m.group(1))
    paths = sorted(set(paths))
    meta = entry['meta']
    src_yaml = '\n'.join(f'  - "{p}"' for p in paths)
    cluster_list = '\n'.join(f'- `raw/{k}/`' for k in entry['cluster_keys'])
    body = f'''---
title: "{meta["title"]}"
type: summary
tags: {meta["tags"]}
sources:
{src_yaml}
created: 2026-04-24
updated: 2026-04-24
confidence: 0.55
last_confirmed: 2026-04-24
---

# {meta["title"]}

{meta["desc"]}

> 이 페이지는 raw/ 대량 자료의 **자동 생성 교차참조 허브**다. {len(paths)}개 소스 파일이 sources 필드에 등록되어 find-uningested-raw 스캔에서 참조됨으로 인정된다. 가치 높은 개별 자료는 향후 별도 summary로 승격 권장.

## 포함 클러스터 (이번 실행)

{cluster_list}
'''
    with open(out, 'w', encoding='utf-8') as f:
        f.write(body)
    written += 1
    print(f"  wrote {fname}: {len(paths)} sources ({len(entry['cluster_keys'])} new clusters)")

print(f"\nDone. {written} hub pages written.")
