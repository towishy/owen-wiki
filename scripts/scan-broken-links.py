"""Scan wiki/ for broken wikilinks."""
import os, re

wiki_pages = set()
for root, dirs, files in os.walk('wiki'):
    for f in files:
        if f.endswith('.md') and f != '_index.md':
            wiki_pages.add(f[:-3])

broken = []
truly_missing = set()
link_pat = re.compile(r'\[\[([^\[\]]+?)\]\]')
code_block_pat = re.compile(r'```.*?```', re.DOTALL)
frontmatter_pat = re.compile(r'\A---.*?---', re.DOTALL)
meta_refs = {'위키링크', 'Source', 'Target', 'page-name', 'PageName', '페이지명', '페이지1', '페이지2'}

for root, dirs, files in os.walk('wiki'):
    for f in files:
        if not f.endswith('.md'):
            continue
        fp = os.path.join(root, f)
        with open(fp, 'r', encoding='utf-8') as fh:
            content = fh.read()
        content_clean = code_block_pat.sub('', content)
        content_clean = frontmatter_pat.sub('', content_clean)

        for m in link_pat.finditer(content_clean):
            raw_target = m.group(1)
            parts = raw_target.split('|')
            target = parts[0].rstrip('\\').strip()
            if target in meta_refs:
                continue
            if target not in wiki_pages:
                broken.append((f, target))
                truly_missing.add(target)

print(f'Broken links: {len(broken)} occurrences, {len(truly_missing)} unique missing targets')
for t in sorted(truly_missing):
    print(f'  - {t}')
