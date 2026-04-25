"""Build raw→wiki reverse map: which wiki page references each raw file.

Output: outputs/drafts/raw-to-wiki-map.json + summary report.

각 wiki 페이지의 sources YAML + 본문의 raw/ 경로 참조를 수집하여 반대 방향 인덱스 구축.
갭 분석에서 "어떤 raw가 아직 활용되지 않았는가" 식별에 사용.
"""
import json
import re
import sys
from pathlib import Path
from collections import defaultdict
from datetime import date

ROOT = Path(__file__).parent.parent
WIKI_ROOT = ROOT / 'wiki'
OUT_JSON = ROOT / 'outputs' / 'drafts' / 'raw-to-wiki-map.json'
OUT_REPORT = ROOT / 'outputs' / 'drafts' / 'raw-to-wiki-map.md'

FM_RE = re.compile(r'^---\n(.*?)\n---', re.DOTALL)
RAW_REF_RE = re.compile(r'(raw/[\w\-./ \u00a0가-힣]+?\.(?:md|pdf|pptx|docx|xlsx|csv))', re.IGNORECASE)


def collect_sources_from_fm(fm_text):
    sources = []
    in_sources = False
    for line in fm_text.splitlines():
        if line.startswith('sources:'):
            rest = line[len('sources:'):].strip()
            if rest.startswith('[') and rest.endswith(']'):
                items = [x.strip().strip('"').strip("'") for x in rest[1:-1].split(',') if x.strip()]
                sources.extend(items)
                in_sources = False
            elif rest == '':
                in_sources = True
            else:
                sources.append(rest.strip('"').strip("'"))
            continue
        if in_sources:
            if line.startswith('  - '):
                sources.append(line[4:].strip().strip('"').strip("'"))
            elif line and not line.startswith(' '):
                in_sources = False
    return sources


def main():
    raw_to_wiki = defaultdict(list)
    wiki_count = 0

    for path in WIKI_ROOT.rglob('*.md'):
        if path.name in ('_index.md', 'README.md'):
            continue
        wiki_count += 1
        try:
            content = path.read_text(encoding='utf-8')
        except Exception:
            continue
        wiki_rel = str(path.relative_to(ROOT)).replace('\\', '/')
        m = FM_RE.match(content)
        sources = []
        if m:
            sources = collect_sources_from_fm(m.group(1))
        # body raw refs
        body_refs = RAW_REF_RE.findall(content)
        all_refs = set()
        for s in sources:
            if s.startswith('raw/') or 'raw/' in s:
                all_refs.add(s.split('raw/', 1)[-1] and 'raw/' + s.split('raw/', 1)[-1])
        for r in body_refs:
            all_refs.add(r)
        for r in all_refs:
            raw_to_wiki[r].append(wiki_rel)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(dict(raw_to_wiki), ensure_ascii=False, indent=2),
                        encoding='utf-8')

    today = date.today().isoformat()
    n_raw = len(raw_to_wiki)
    multi = sum(1 for v in raw_to_wiki.values() if len(v) > 1)
    lines = [
        '---', 'title: "Raw → Wiki 역참조 맵"', 'type: report',
        f'updated: {today}', f'count: {n_raw}', '---', '',
        f'# Raw → Wiki 역참조 맵 — {n_raw} raw 파일',
        '',
        f'- 총 wiki 페이지 스캔: {wiki_count}',
        f'- 참조된 raw 파일: {n_raw}',
        f'- 다중 참조 raw 파일: {multi} (2+ wiki 페이지가 인용)',
        '',
        '## Top 20 다중 참조 raw 파일',
        '',
        '| Raw 파일 | 참조 wiki 수 |',
        '|----------|--------------|',
    ]
    top = sorted(raw_to_wiki.items(), key=lambda kv: -len(kv[1]))[:20]
    for r, wikis in top:
        lines.append(f'| `{r}` | {len(wikis)} |')
    OUT_REPORT.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    print(f'Wiki pages: {wiki_count}')
    print(f'Distinct raw files referenced: {n_raw}')
    print(f'Multi-referenced raw files: {multi}')
    print(f'JSON: {OUT_JSON}')
    print(f'Report: {OUT_REPORT}')


if __name__ == '__main__':
    main()
