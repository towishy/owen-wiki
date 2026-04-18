"""Check tag prefix compliance across all wiki pages."""
import os, re

valid_prefixes = ('prod/', 'customer/', 'type/', 'topic/', 'series/')
prefix_ok = 0
prefix_bad = 0
bad_pages = []

for root, dirs, files in os.walk('wiki'):
    if 'ontology' in root:
        continue
    for f in files:
        if not f.endswith('.md') or f in ('_index.md', 'README.md'):
            continue
        fp = os.path.join(root, f)
        with open(fp, 'r', encoding='utf-8') as fh:
            content = fh.read()
        m = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if not m:
            continue
        fm_text = m.group(1)
        tags_match = re.search(r'tags:\s*\[([^\]]*)\]', fm_text)
        if not tags_match:
            continue
        tags_raw = tags_match.group(1)
        tags = [t.strip().strip('"').strip("'") for t in tags_raw.split(',') if t.strip()]

        bad_tags = [t for t in tags if not any(t.startswith(p) for p in valid_prefixes)]
        if bad_tags:
            prefix_bad += 1
            bad_pages.append((f, bad_tags))
        else:
            prefix_ok += 1

print(f'Tag prefix compliance: {prefix_ok} OK, {prefix_bad} non-compliant')
if bad_pages:
    print()
    for page, tags in sorted(bad_pages):
        print(f'  {page}: {tags}')
