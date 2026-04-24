"""Analyze large hub pages and propose split strategy.

50KB 초과 wiki 페이지를 식별하고 sources YAML의 클러스터 키로 sub-hub 분할 계획 제안.

사용:
  python scripts/analyze-large-hubs.py            # 50KB 이상 보고
  python scripts/analyze-large-hubs.py --threshold 30000   # 임계값 변경
"""
import re
import sys
from pathlib import Path
from collections import Counter
from datetime import date

ROOT = Path(__file__).parent.parent
WIKI = ROOT / 'wiki'
OUT = ROOT / 'outputs' / 'drafts' / 'large-hubs-split-plan.md'

THRESHOLD = 50_000
for i, a in enumerate(sys.argv):
    if a == '--threshold' and i + 1 < len(sys.argv):
        THRESHOLD = int(sys.argv[i + 1])

FM_RE = re.compile(r'^---\n(.*?)\n---', re.DOTALL)


def cluster_key(src_path, depth=3):
    parts = src_path.split('/')
    if parts[0] == 'raw':
        parts = parts[1:]
    return '/'.join(parts[:depth])


def main():
    huge = []
    for p in WIKI.rglob('*.md'):
        if p.name in ('_index.md', 'README.md'):
            continue
        size = p.stat().st_size
        if size >= THRESHOLD:
            huge.append((p, size))
    huge.sort(key=lambda x: -x[1])

    today = date.today().isoformat()
    lines = [
        '---', f'title: "Large Hub Split Plan — {today}"', 'type: report',
        f'updated: {today}', f'count: {len(huge)}', '---', '',
        f'# Large Hub Split Plan ({THRESHOLD/1024:.0f}KB+ wiki pages)',
        '',
        f'총 {len(huge)} 페이지가 임계값 초과.',
        '',
    ]

    for path, size in huge:
        rel = str(path.relative_to(ROOT)).replace('\\', '/')
        content = path.read_text(encoding='utf-8')
        m = FM_RE.match(content)
        sources = []
        if m:
            in_src = False
            for line in m.group(1).splitlines():
                if line.startswith('sources:'):
                    in_src = True
                    rest = line.split(':', 1)[1].strip()
                    if rest and rest != '[]':
                        if rest.startswith('['):
                            for x in rest[1:-1].split(','):
                                sources.append(x.strip().strip('"').strip("'"))
                            in_src = False
                    continue
                if in_src:
                    if line.startswith('  - '):
                        sources.append(line[4:].strip().strip('"').strip("'"))
                    elif line and not line.startswith(' '):
                        in_src = False
        clusters = Counter(cluster_key(s) for s in sources if s.startswith('raw/'))

        lines.append(f'## {Path(rel).stem}')
        lines.append('')
        lines.append(f'- 경로: `{rel}`')
        lines.append(f'- 크기: {size/1024:.1f} KB')
        lines.append(f'- sources 항목: {len(sources)}')
        lines.append(f'- 추천 sub-hub 후보 (클러스터 키, 5개 이상):')
        lines.append('')
        lines.append('| 클러스터 | sources 수 | sub-hub 후보명 |')
        lines.append('|----------|-----------|-----------------|')
        for ck, cnt in clusters.most_common(15):
            if cnt < 5:
                continue
            slug = ck.lower().replace('/', '-').replace(' ', '-').replace('_', '-')[:60]
            stem = Path(rel).stem
            sub_name = f'{stem}-{slug}'
            lines.append(f'| `{ck}` | {cnt} | `{sub_name}` |')
        lines.append('')

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'Found {len(huge)} large pages (>= {THRESHOLD/1024:.0f}KB)')
    for path, size in huge[:10]:
        print(f'  {size/1024:7.1f}KB  {path.relative_to(ROOT)}')
    print(f'\nPlan: {OUT}')


if __name__ == '__main__':
    main()
