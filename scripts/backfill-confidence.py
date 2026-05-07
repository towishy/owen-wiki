"""Backfill `confidence` and `last_confirmed` for wiki pages missing them.

AGENTS.md v1.4+ 신규 페이지부터 confidence/last_confirmed 권장이지만, 기존 페이지에
미적용 다수. 본 스크립트는 메타데이터 휴리스틱으로 자동 채워준다.

휴리스틱 (AGENTS.md Confidence Scoring 가이드 기반):
  - sources 5개 이상 + type=summary/synthesis/comparison → 0.85
  - sources 3-4개                                          → 0.75
  - sources 1-2개 (대부분의 entity/concept)                → 0.65
  - sources 0개 + 본문 < 500자 (stub)                      → 0.40
  - 본문 < 100자                                           → 0.30 + tag/stub 권장

last_confirmed가 없으면 updated 값 사용.

사용:
  python scripts/backfill-confidence.py            # 보고만
  python scripts/backfill-confidence.py --apply    # 실제 적용
  python scripts/backfill-confidence.py --apply --only-missing  # 기존 값 유지
"""
import os
import re
import sys
from pathlib import Path

WIKI_ROOT = Path(__file__).parent.parent / 'wiki'
APPLY = '--apply' in sys.argv
ONLY_MISSING = '--only-missing' in sys.argv or True  # 기본값: 안전하게 missing만

FM_RE = re.compile(r'^---\n(.*?)\n---\n(.*)$', re.DOTALL)


def parse_fm(content):
    m = FM_RE.match(content)
    if not m:
        return None, content
    fm_text = m.group(1)
    body = m.group(2)
    fm = {}
    cur_key = None
    cur_list = None
    for line in fm_text.splitlines():
        if cur_list is not None and line.startswith('  - '):
            cur_list.append(line[4:].strip().strip('"').strip("'"))
            continue
        else:
            cur_list = None
        m2 = re.match(r'^([a-zA-Z_]+):\s*(.*)$', line)
        if m2:
            k, v = m2.group(1), m2.group(2).strip()
            if v == '':
                cur_list = []
                fm[k] = cur_list
            elif v.startswith('[') and v.endswith(']'):
                fm[k] = [x.strip().strip('"').strip("'") for x in v[1:-1].split(',') if x.strip()]
            else:
                fm[k] = v.strip('"').strip("'")
            cur_key = k
    return fm, body


def estimate_confidence(fm, body):
    sources = fm.get('sources', [])
    if isinstance(sources, str):
        sources = [sources]
    n_src = len(sources) if sources else 0
    body_len = len(body.strip())
    ptype = fm.get('type', '')
    tags = fm.get('tags', [])
    if isinstance(tags, str):
        tags = [tags]

    if body_len < 100:
        return 0.30, 'stub-very-short'
    if n_src == 0 and body_len < 500:
        return 0.40, 'stub-no-source'
    if n_src >= 5 and ptype in ('summary', 'synthesis', 'comparison'):
        return 0.85, 'rich-summary'
    if n_src >= 3:
        return 0.75, 'multi-source'
    if n_src >= 1:
        return 0.65, 'single-source'
    return 0.50, 'default'


def serialize_fm(fm):
    """Reserialize frontmatter preserving common ordering."""
    order = ['title', 'type', 'tags', 'sources', 'created', 'updated',
             'confidence', 'last_confirmed', 'stale_after',
             'supersedes', 'superseded_by', 'count']
    lines = []
    seen = set()
    for k in order:
        if k in fm:
            seen.add(k)
            v = fm[k]
            if isinstance(v, list):
                if not v:
                    lines.append(f'{k}: []')
                else:
                    lines.append(f'{k}:')
                    for item in v:
                        lines.append(f'  - "{item}"')
            else:
                lines.append(f'{k}: {v}')
    for k, v in fm.items():
        if k in seen:
            continue
        if isinstance(v, list):
            if not v:
                lines.append(f'{k}: []')
            else:
                lines.append(f'{k}:')
                for item in v:
                    lines.append(f'  - "{item}"')
        else:
            lines.append(f'{k}: {v}')
    return '\n'.join(lines)


def main():
    changed = 0
    skipped = 0
    reports = {'stub-very-short': 0, 'stub-no-source': 0, 'rich-summary': 0,
               'multi-source': 0, 'single-source': 0, 'default': 0}
    for path in WIKI_ROOT.rglob('*.md'):
        if path.name in ('_index.md', 'README.md'):
            continue
        if 'ontology' in path.parts:
            continue
        try:
            content = path.read_text(encoding='utf-8')
        except Exception as e:
            print(f'ERR  {path}: {e}')
            continue
        fm, body = parse_fm(content)
        if fm is None:
            continue
        has_conf = 'confidence' in fm
        has_lc = 'last_confirmed' in fm
        if has_conf and has_lc and ONLY_MISSING:
            skipped += 1
            continue
        score, reason = estimate_confidence(fm, body)
        reports[reason] += 1
        if not has_conf:
            fm['confidence'] = f'{score:.2f}'
        if not has_lc:
            fm['last_confirmed'] = fm.get('updated', '2026-04-24')
        if APPLY:
            new_content = '---\n' + serialize_fm(fm) + '\n---\n' + body
            path.write_text(new_content, encoding='utf-8')
        changed += 1
    mode = 'APPLIED' if APPLY else 'DRY-RUN'
    print(f'\n[{mode}] backfilled: {changed} pages, skipped (already set): {skipped}')
    for k, v in reports.items():
        print(f'  {k}: {v}')


if __name__ == '__main__':
    main()
