"""Detect orphan wiki pages (0 inbound wikilinks from other pages)."""
import os, re

# Collect all wiki page names
wiki_pages = {}
for root, dirs, files in os.walk('wiki'):
    if 'ontology' in root:
        continue
    for f in files:
        if f.endswith('.md') and f not in ('_index.md', 'README.md'):
            name = f[:-3]
            cat = os.path.basename(root)
            wiki_pages[name] = cat

# Count inbound links for each page
inbound = {name: 0 for name in wiki_pages}
link_pat = re.compile(r'\[\[([^\[\]]+?)\]\]')
code_block_pat = re.compile(r'```.*?```', re.DOTALL)

for root, dirs, files in os.walk('wiki'):
    if 'ontology' in root:
        continue
    for f in files:
        if not f.endswith('.md'):
            continue
        fp = os.path.join(root, f)
        source_name = f[:-3] if f.endswith('.md') else f
        with open(fp, 'r', encoding='utf-8') as fh:
            content = fh.read()
        content_clean = code_block_pat.sub('', content)

        seen_in_file = set()
        for m in link_pat.finditer(content_clean):
            raw = m.group(1)
            target = raw.split('|')[0].rstrip('\\').strip()
            if target != source_name and target in inbound and target not in seen_in_file:
                inbound[target] += 1
                seen_in_file.add(target)

orphans = [(name, cat) for name, cat in wiki_pages.items() if inbound.get(name, 0) == 0]
orphans.sort(key=lambda x: (x[1], x[0]))

print(f"Orphan pages (0 inbound links): {len(orphans)}")
for name, cat in orphans:
    print(f"  [{cat}] {name}")

print(f"\nTotal pages: {len(wiki_pages)}, With links: {len(wiki_pages) - len(orphans)}")
