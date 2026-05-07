"""Detect wikilink patterns that pollute graph nodes."""
import json
import sys
from collections import Counter
from datetime import date

from wiki_utils import OUTPUTS_ROOT, extract_raw_wikilinks, iter_wiki_pages, normalize_wikilink_target, page_slugs

OUT_JSON = OUTPUTS_ROOT / 'wiki-ops' / 'graph-hygiene.json'
OUT_MD = OUTPUTS_ROOT / 'wiki-ops' / 'graph-hygiene.md'

PLACEHOLDERS = {'페이지명', '페이지1', '페이지2', 'page-name', 'pagename', 'todo', 'example', 'sample', '예시', '샘플'}
META_REFS = {'위키링크', 'Source', 'Target', '_index'} | PLACEHOLDERS


def classify():
    known = page_slugs(include_indexes=True)
    issues = []
    escaped_aliases = 0
    for page in iter_wiki_pages(include_indexes=True):
        for raw in extract_raw_wikilinks(page['content']):
            target = normalize_wikilink_target(raw)
            if '\\|' in raw:
                escaped_aliases += 1
            if target.lower() in PLACEHOLDERS or target in PLACEHOLDERS:
                issues.append({'type': 'placeholder', 'path': page['path'], 'source': page['slug'], 'raw': raw, 'target': target})
                continue
            if raw.split('|', 1)[0].strip().endswith('\\') and '\\|' not in raw:
                issues.append({'type': 'trailing-backslash', 'path': page['path'], 'source': page['slug'], 'raw': raw, 'target': target})
                continue
            if target and target not in known and target not in META_REFS:
                issues.append({'type': 'unknown-target', 'path': page['path'], 'source': page['slug'], 'raw': raw, 'target': target})
    return issues, escaped_aliases


def render(issues, escaped_aliases):
    today = date.today().isoformat()
    counts = Counter(issue['type'] for issue in issues)
    lines = [
        '---', 'title: "Graph Hygiene"', 'type: report', f'updated: {today}', '---', '',
        f'# Graph Hygiene — {today}', '',
        f'- Blocking issues: `{len(issues)}`',
        f'- Escaped table aliases normalized by parser: `{escaped_aliases}`', '',
        '## Issue Counts', '', '| Type | Count |', '|---|---:|',
    ]
    for issue_type, count in counts.most_common():
        lines.append(f'| `{issue_type}` | {count} |')
    if not counts:
        lines.append('| - | 0 |')
    lines += ['', '## Top Issues', '', '| Type | Source | Target | Raw | Path |', '|---|---|---|---|---|']
    for issue in issues[:50]:
        lines.append(f"| `{issue['type']}` | [[{issue['source']}]] | `{issue['target']}` | `{issue['raw']}` | `{issue['path']}` |")
    if not issues:
        lines.append('| - | - | - | - | - |')
    return '\n'.join(lines) + '\n'


def main():
    issues, escaped_aliases = classify()
    payload = {'updated': date.today().isoformat(), 'issues': issues, 'issue_count': len(issues), 'escaped_aliases': escaped_aliases}
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    OUT_MD.write_text(render(issues, escaped_aliases), encoding='utf-8')
    print(f'Graph hygiene issues: {len(issues)}')
    print(f'Escaped aliases normalized: {escaped_aliases}')
    print(f'Report: {OUT_MD}')
    if issues:
        sys.exit(1)


if __name__ == '__main__':
    main()