"""Check ontology consistency: all nodes in ontology files should be actual wiki pages."""
import os, re

# Collect all wiki page names
wiki_pages = set()
for root, dirs, files in os.walk('wiki'):
    if 'ontology' in root:
        continue
    for f in files:
        if f.endswith('.md') and f not in ('_index.md', 'README.md'):
            wiki_pages.add(f[:-3])

# Check each ontology file
link_pat = re.compile(r'\[\[([^\[\]|]+?)(?:\|[^\]]+?)?\]\]')
meta_refs = {'위키링크', 'Source', 'Target', 'page-name', 'PageName', '페이지명', '페이지1', '페이지2'}

ontology_dir = os.path.join('wiki', 'ontology')
if not os.path.isdir(ontology_dir):
    print('wiki/ontology/ directory not found')
    exit(1)

for f in sorted(os.listdir(ontology_dir)):
    if not f.endswith('.md'):
        continue
    fp = os.path.join(ontology_dir, f)
    with open(fp, 'r', encoding='utf-8') as fh:
        content = fh.read()

    refs = set()
    missing = set()
    for m in link_pat.finditer(content):
        target = m.group(1).rstrip('\\').strip()
        if target in meta_refs:
            continue
        refs.add(target)
        if target not in wiki_pages:
            missing.add(target)

    if missing:
        print(f"{f}: {len(refs)} refs, {len(missing)} MISSING")
        for t in sorted(missing):
            print(f"  - {t}")
    else:
        print(f"{f}: {len(refs)} refs, all OK")
