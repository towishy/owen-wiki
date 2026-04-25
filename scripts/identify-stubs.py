"""Identify stub wiki pages and report (or tag).

기준 (어느 하나라도 해당되면 stub):
  - 본문(YAML 제외) < 200자
  - sources 0개 + 본문 < 800자
  - 헤딩(##) 1개 이하 + 본문 < 500자

출력: outputs/drafts/stub-pages-report.md (수동 보강 큐)

사용:
  python scripts/identify-stubs.py            # 보고만
  python scripts/identify-stubs.py --tag      # tag/stub + confidence 0.30 적용
"""
import os
import re
import sys
from pathlib import Path
from datetime import date

WIKI_ROOT = Path(__file__).parent.parent / 'wiki'
OUT_PATH = Path(__file__).parent.parent / 'outputs' / 'drafts' / 'stub-pages-report.md'
APPLY = '--tag' in sys.argv

FM_RE = re.compile(r'^---\n(.*?)\n---\n(.*)$', re.DOTALL)


def parse_fm(content):
    m = FM_RE.match(content)
    if not m:
        return {}, content
    fm = {}
    for line in m.group(1).splitlines():
        m2 = re.match(r'^([a-zA-Z_]+):\s*(.*)$', line)
        if m2:
            fm[m2.group(1)] = m2.group(2).strip()
    return fm, m.group(2)


def is_stub(fm, body):
    body_clean = body.strip()
    n_chars = len(body_clean)
    n_h2 = body_clean.count('\n## ')
    sources_line = fm.get('sources', '')
    n_src_approx = sources_line.count(',') + 1 if sources_line and sources_line != '[]' else 0
    if 'sources' in fm and fm.get('sources') == '':
        # multiline sources, count from full content
        pass
    if n_chars < 200:
        return True, 'very-short'
    if n_src_approx == 0 and n_chars < 800:
        return True, 'no-source-short'
    if n_h2 <= 1 and n_chars < 500:
        return True, 'no-structure'
    return False, None


def main():
    stubs = []
    total = 0
    for path in WIKI_ROOT.rglob('*.md'):
        if path.name in ('_index.md', 'README.md'):
            continue
        if 'ontology' in path.parts:
            continue
        try:
            content = path.read_text(encoding='utf-8')
        except Exception:
            continue
        total += 1
        fm, body = parse_fm(content)
        stub, reason = is_stub(fm, body)
        if stub:
            rel = str(path.relative_to(WIKI_ROOT.parent)).replace('\\', '/')
            stubs.append((rel, reason, len(body.strip()), fm.get('title', path.stem)))

    stubs.sort(key=lambda x: (x[1], x[2]))
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    lines = [
        '---',
        'title: "Stub 페이지 보강 큐"',
        'type: report',
        f'updated: {today}',
        f'count: {len(stubs)}',
        '---',
        '',
        f'# Stub 페이지 보강 큐 — {len(stubs)} / {total}',
        '',
        '> AGENTS.md Lint 워크플로 결과. 우선 보강 대상.',
        '',
        '| 페이지 | 사유 | 본문(자) |',
        '|--------|------|----------|',
    ]
    for rel, reason, n, title in stubs:
        link = f'[[{Path(rel).stem}|{title}]]'
        lines.append(f'| {link} | `{reason}` | {n} |')
    OUT_PATH.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    print(f'Stubs found: {len(stubs)} / {total}')
    print(f'Report: {OUT_PATH}')
    by_reason = {}
    for _, r, _, _ in stubs:
        by_reason[r] = by_reason.get(r, 0) + 1
    for r, n in by_reason.items():
        print(f'  {r}: {n}')

    if APPLY:
        # tag/stub 자동 부여는 위험 — 사용자가 직접 검토 후 backfill-confidence.py 실행 권장
        print('\n--tag 옵션은 안전을 위해 미구현. 보고서 기반 수동 보강 후 backfill-confidence.py 사용 권장.')


if __name__ == '__main__':
    main()
