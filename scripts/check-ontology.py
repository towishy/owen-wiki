"""Check ontology consistency: all nodes in ontology files should be actual wiki pages.

추가 검증 (v2):
  - supersedes / superseded_by 양방향 일관성
  - 관계코드 표준화 (정규 사전 외 사용 시 경고)
"""
import os, re

# 표준 관계코드 (AGENTS.md §트리플렛 추출 프로토콜 + 위키 실사용 관계)
CANONICAL_RELATIONS = {
    # 기본 (AGENTS.md)
    'uses', 'integrates-with', 'deployed-at', 'competes-with', 'related-to',
    'part-of', 'depends-on', 'supersedes', 'superseded-by',
    # 확장 — 구조
    'subset-of', 'implements', 'replaces', 'extends', 'consumes', 'produces',
    'contains', 'aggregates', 'has-feature',
    # 확장 — 시스템 동작
    'triggers', 'enables', 'requires', 'supports', 'deploys',
    'feeds', 'receives-signal-from', 'uses-signal', 'audited-via',
    # 확장 — 콘텐츠
    'covers', 'documents', 'teaches', 'solves',
}

# Collect all wiki page names + frontmatter for supersession
wiki_pages = set()
fm_supersedes = {}      # page → set(target page names)
fm_superseded_by = {}   # page → set(source page names)
fm_re = re.compile(r'^---\n(.*?)\n---', re.DOTALL)
list_re = re.compile(r'\[\[([^\[\]|]+?)(?:\|[^\]]+?)?\]\]')

for root, dirs, files in os.walk('wiki'):
    if 'ontology' in root:
        continue
    for f in files:
        if f.endswith('.md') and f not in ('_index.md', 'README.md'):
            name = f[:-3]
            wiki_pages.add(name)
            try:
                content = open(os.path.join(root, f), encoding='utf-8').read()
            except Exception:
                continue
            m = fm_re.match(content)
            if not m:
                continue
            for line in m.group(1).splitlines():
                if line.startswith('supersedes:'):
                    targets = set(list_re.findall(line))
                    if targets:
                        fm_supersedes[name] = targets
                elif line.startswith('superseded_by:'):
                    targets = set(list_re.findall(line))
                    if targets:
                        fm_superseded_by[name] = targets

# === Bidirectional supersession consistency ===
print('=== Supersession Consistency ===')
issues = 0
for src, targets in fm_supersedes.items():
    for tgt in targets:
        if tgt not in fm_superseded_by or src not in fm_superseded_by[tgt]:
            print(f'  ⚠  [[{src}]] supersedes [[{tgt}]] but [[{tgt}]] missing superseded_by')
            issues += 1
for tgt, sources in fm_superseded_by.items():
    for src in sources:
        if src not in fm_supersedes or tgt not in fm_supersedes[src]:
            print(f'  ⚠  [[{tgt}]] superseded_by [[{src}]] but [[{src}]] missing supersedes')
            issues += 1
if issues == 0:
    print('  ✅ All supersession links consistent')
print()

# Check each ontology file
link_pat = re.compile(r'\[\[([^\[\]|]+?)(?:\|[^\]]+?)?\]\]')
relation_pat = re.compile(r'\]\]\s*\[([a-z\-]+)\]\s*\[\[')
meta_refs = {'위키링크', 'Source', 'Target', 'page-name', 'PageName', '페이지명', '페이지1', '페이지2'}

ontology_dir = 'wiki/ontology'
nonstandard_relations = set()
for f in sorted(os.listdir(ontology_dir)):
    if not f.endswith('.md'):
        continue
    fp = os.path.join(ontology_dir, f)
    with open(fp, 'r', encoding='utf-8') as fh:
        content = fh.read()
    
    # Extract all wikilink references
    refs = set()
    missing = set()
    for m in link_pat.finditer(content):
        target = m.group(1).rstrip('\\').strip()
        if target in meta_refs:
            continue
        refs.add(target)
        if target not in wiki_pages:
            missing.add(target)

    # Extract relation codes
    for m in relation_pat.finditer(content):
        rel = m.group(1)
        if rel not in CANONICAL_RELATIONS:
            nonstandard_relations.add((f, rel))

    if missing:
        print(f"{f}: {len(refs)} refs, {len(missing)} MISSING")
        for t in sorted(missing):
            print(f"  - {t}")
    else:
        print(f"{f}: {len(refs)} refs, all OK")

if nonstandard_relations:
    print('\n=== Non-Standard Relation Codes ===')
    for f, rel in sorted(nonstandard_relations):
        print(f'  ⚠  {f}: [{rel}]  (표준: {sorted(CANONICAL_RELATIONS)})')
else:
    print('\n=== Relation Codes: ✅ all canonical ===')
