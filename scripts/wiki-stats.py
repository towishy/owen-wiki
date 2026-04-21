"""Wiki repository statistics."""
import os, re, subprocess
from collections import Counter

cats = ['entities', 'concepts', 'summaries', 'comparisons', 'synthesis']
cat_counts = {}
total_wiki = 0
for c in cats:
    d = os.path.join('wiki', c)
    files = [f for f in os.listdir(d) if f.endswith('.md') and f not in ('_index.md', 'README.md')]
    cat_counts[c] = len(files)
    total_wiki += len(files)

ont_files = [f for f in os.listdir('wiki/ontology') if f.endswith('.md')]
ont_count = len(ont_files)

# Tag statistics
all_tags = Counter()
prod_tags = Counter()
customer_tags = Counter()
topic_tags = Counter()
type_tags = Counter()
series_tags = Counter()
page_count_with_tags = 0

# Confidence / lifecycle (v1.4.0+)
conf_buckets = {'0.95-1.0': 0, '0.80-0.94': 0, '0.65-0.79': 0, '0.40-0.64': 0, '<0.40': 0, 'unset': 0}
superseded_count = 0
aging_count = 0
stale_count = 0

for root, dirs, files in os.walk('wiki'):
    if 'ontology' in root:
        continue
    for f in files:
        if not f.endswith('.md') or f in ('_index.md', 'README.md'):
            continue
        fp = os.path.join(root, f)
        with open(fp, 'r', encoding='utf-8') as fh:
            content = fh.read()
        m = re.search(r'tags:\s*\[([^\]]*)\]', content)
        if not m:
            continue
        page_count_with_tags += 1
        raw_tags = m.group(1)
        tags = [t.strip().strip('"').strip("'") for t in raw_tags.split(',') if t.strip()]
        for t in tags:
            all_tags[t] += 1
            if t.startswith('prod/'): prod_tags[t] += 1
            elif t.startswith('customer/'): customer_tags[t] += 1
            elif t.startswith('topic/'): topic_tags[t] += 1
            elif t.startswith('type/'): type_tags[t] += 1
            elif t.startswith('series/'): series_tags[t] += 1
        if 'aging' in tags: aging_count += 1
        if 'stale' in tags: stale_count += 1

        # confidence
        cm = re.search(r'^confidence:\s*([0-9.]+)', content, re.MULTILINE)
        if cm:
            try:
                v = float(cm.group(1))
                if v >= 0.95: conf_buckets['0.95-1.0'] += 1
                elif v >= 0.80: conf_buckets['0.80-0.94'] += 1
                elif v >= 0.65: conf_buckets['0.65-0.79'] += 1
                elif v >= 0.40: conf_buckets['0.40-0.64'] += 1
                else: conf_buckets['<0.40'] += 1
            except ValueError:
                conf_buckets['unset'] += 1
        else:
            conf_buckets['unset'] += 1

        sm = re.search(r'^superseded_by:\s*(\S.*)', content, re.MULTILINE)
        if sm and sm.group(1).strip() not in ('""', "''", '[]'):
            superseded_count += 1

# Wikilink density
total_links = 0
link_pat = re.compile(r'\[\[([^\[\]]+?)\]\]')
for root, dirs, files in os.walk('wiki'):
    for f in files:
        if not f.endswith('.md'):
            continue
        fp = os.path.join(root, f)
        with open(fp, 'r', encoding='utf-8') as fh:
            content = fh.read()
        total_links += len(link_pat.findall(content))

# Content size
total_words = 0
total_lines = 0
for root, dirs, files in os.walk('wiki'):
    for f in files:
        if not f.endswith('.md'):
            continue
        fp = os.path.join(root, f)
        with open(fp, 'r', encoding='utf-8') as fh:
            lines = fh.readlines()
        total_lines += len(lines)
        total_words += sum(len(line.split()) for line in lines)

# Raw source stats
raw_count = 0
raw_size = 0
for root, dirs, files in os.walk('raw'):
    for f in files:
        raw_count += 1
        try:
            raw_size += os.path.getsize(os.path.join(root, f))
        except:
            pass

# Git commit count
result = subprocess.run(['git', 'log', '--oneline'], capture_output=True, text=True, encoding='utf-8', errors='replace')
commit_count = len(result.stdout.strip().split('\n')) if result.stdout and result.stdout.strip() else 0

print('=== WIKI REPOSITORY STATISTICS ===')
print()
print('## Pages')
for c in cats:
    print(f'  {c:15s}: {cat_counts[c]:>4d}')
print(f'  {"ontology":15s}: {ont_count:>4d}')
print(f'  {"───────────────":15s}  {"────":>4s}')
print(f'  {"TOTAL":15s}: {total_wiki + ont_count:>4d}')
print()
print('## Content')
print(f'  Total lines:    {total_lines:>8,d}')
print(f'  Total words:    {total_words:>8,d}')
print(f'  Wikilinks:      {total_links:>8,d}')
print(f'  Avg links/page: {total_links / (total_wiki + ont_count):.1f}')
print()
print('## Tags')
print(f'  Pages with tags:  {page_count_with_tags}')
print(f'  Unique tags:      {len(all_tags)}')
print(f'  prod/ tags:       {len(prod_tags)} ({sum(prod_tags.values())} uses)')
print(f'  customer/ tags:   {len(customer_tags)} ({sum(customer_tags.values())} uses)')
print(f'  topic/ tags:      {len(topic_tags)} ({sum(topic_tags.values())} uses)')
print(f'  type/ tags:       {len(type_tags)} ({sum(type_tags.values())} uses)')
print(f'  series/ tags:     {len(series_tags)} ({sum(series_tags.values())} uses)')
print()
print('## Confidence & Lifecycle (v1.4.0)')
for bucket, n in conf_buckets.items():
    print(f'  {bucket:12s}: {n:>4d}')
print(f'  superseded  : {superseded_count}')
print(f'  aging tag   : {aging_count}')
print(f'  stale tag   : {stale_count}')
print()
print('## Raw Sources')
print(f'  Files:            {raw_count:,d}')
print(f'  Size:             {raw_size / (1024**3):.1f} GB')
print()
print('## Git')
print(f'  Commits:          {commit_count}')
print()
print('## Top prod/ tags (product coverage)')
for tag, cnt in prod_tags.most_common(30):
    print(f'  {tag:40s} {cnt:>3d} pages')
print()
print('## Top topic/ tags')
for tag, cnt in topic_tags.most_common(20):
    print(f'  {tag:40s} {cnt:>3d} pages')
print()
print('## customer/ tags')
for tag, cnt in customer_tags.most_common(40):
    print(f'  {tag:40s} {cnt:>3d} pages')
