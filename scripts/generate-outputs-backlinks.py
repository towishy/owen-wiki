"""Add `## 파생 산출물` section to wiki pages referenced by outputs/*.md.

스캔: outputs/ 모든 md → 위키링크 [[페이지명]] 추출 → wiki/ 해당 페이지 끝에 백링크 섹션 추가/갱신.

사용:
  python scripts/generate-outputs-backlinks.py            # 보고만
  python scripts/generate-outputs-backlinks.py --apply    # 실제 적용
"""
import re
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
OUTPUTS = ROOT / 'outputs'
WIKI = ROOT / 'wiki'
APPLY = '--apply' in sys.argv

LINK_RE = re.compile(r'\[\[([^\[\]|#]+?)(?:\|[^\[\]]*)?(?:#[^\[\]]*)?\]\]')
SECTION_HEADER = '## 파생 산출물'
MARK_BEGIN = '<!-- AUTO:OUTPUTS-BACKLINKS:BEGIN -->'
MARK_END = '<!-- AUTO:OUTPUTS-BACKLINKS:END -->'


def index_wiki_pages():
    pages = {}
    for p in WIKI.rglob('*.md'):
        if p.name in ('_index.md', 'README.md'):
            continue
        if 'ontology' in p.parts:
            continue
        pages[p.stem] = p
    return pages


def main():
    if not OUTPUTS.exists():
        print('outputs/ not found')
        return
    pages = index_wiki_pages()
    backlinks = defaultdict(set)
    for op in OUTPUTS.rglob('*.md'):
        try:
            content = op.read_text(encoding='utf-8')
        except Exception:
            continue
        rel = str(op.relative_to(ROOT)).replace('\\', '/')
        for m in LINK_RE.finditer(content):
            target = m.group(1).strip()
            if target in pages:
                backlinks[target].add(rel)

    print(f'Wiki pages with output backlinks: {len(backlinks)}')
    if not APPLY:
        for tgt, srcs in sorted(backlinks.items())[:10]:
            print(f'  {tgt}: {len(srcs)} outputs')
        print('\n(--apply 옵션으로 실제 적용)')
        return

    updated = 0
    for tgt, srcs in backlinks.items():
        path = pages[tgt]
        content = path.read_text(encoding='utf-8')
        block_lines = [MARK_BEGIN, SECTION_HEADER, '']
        for s in sorted(srcs):
            stem = Path(s).stem
            block_lines.append(f'- [{stem}]({s})')
        block_lines.append(MARK_END)
        block = '\n'.join(block_lines)

        if MARK_BEGIN in content and MARK_END in content:
            content = re.sub(
                re.escape(MARK_BEGIN) + r'.*?' + re.escape(MARK_END),
                block, content, count=1, flags=re.DOTALL,
            )
        else:
            if not content.endswith('\n'):
                content += '\n'
            content += '\n' + block + '\n'
        path.write_text(content, encoding='utf-8')
        updated += 1
    print(f'Applied to {updated} wiki pages')


if __name__ == '__main__':
    main()
