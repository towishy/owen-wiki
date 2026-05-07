"""Shared helpers for wiki maintenance scripts."""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
WIKI_ROOT = ROOT / 'wiki'
OUTPUTS_ROOT = ROOT / 'outputs'
WIKI_CATEGORIES = ('entities', 'concepts', 'summaries', 'comparisons', 'synthesis', 'ontology')

RAW_WIKILINK_RE = re.compile(r'\[\[([^\[\]]+?)\]\]')
CODE_BLOCK_RE = re.compile(r'```.*?```', re.DOTALL)
FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---', re.DOTALL)
TOKEN_RE = re.compile(r'[0-9A-Za-z가-힣][0-9A-Za-z가-힣_-]*')


def md_cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')


def strip_noncontent(text):
    text = CODE_BLOCK_RE.sub('', text)
    return FRONTMATTER_RE.sub('', text)


def normalize_wikilink_target(raw_target):
    target = raw_target.replace('\\|', '|').strip()
    target = target.split('|', 1)[0].split('#', 1)[0].strip()
    return target.rstrip('\\').strip()


def extract_wikilink_targets(text):
    cleaned = strip_noncontent(text)
    return [normalize_wikilink_target(match.group(1)) for match in RAW_WIKILINK_RE.finditer(cleaned)]


def extract_raw_wikilinks(text):
    cleaned = strip_noncontent(text)
    return [match.group(1).strip() for match in RAW_WIKILINK_RE.finditer(cleaned)]


def parse_inline_list(value):
    value = value.strip()
    if not (value.startswith('[') and value.endswith(']')):
        return []
    inner = value[1:-1].strip()
    if not inner:
        return []
    return [item.strip().strip('"').strip("'") for item in inner.split(',') if item.strip()]


def parse_frontmatter(content):
    match = FRONTMATTER_RE.match(content)
    if not match:
        return {}, content
    meta = {'tags': [], 'sources': []}
    current_key = None
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        if line.startswith('  - ') and current_key in ('tags', 'sources'):
            meta[current_key].append(line[4:].strip().strip('"').strip("'"))
            continue
        current_key = None
        if ':' not in line:
            continue
        key, raw_value = line.split(':', 1)
        key = key.strip()
        value = raw_value.strip()
        if key in ('tags', 'sources'):
            current_key = key
            if value.startswith('['):
                meta[key].extend(parse_inline_list(value))
            elif value:
                meta[key].append(value.strip('"').strip("'"))
        else:
            meta[key] = value.strip('"').strip("'")
    return meta, content[match.end():]


def iter_wiki_pages(include_indexes=False):
    for path in sorted(WIKI_ROOT.rglob('*.md')):
        if not include_indexes and path.name in ('_index.md', 'README.md'):
            continue
        rel = path.relative_to(ROOT).as_posix()
        parts = path.relative_to(WIKI_ROOT).parts
        category = parts[0] if len(parts) > 1 else '_root'
        content = path.read_text(encoding='utf-8', errors='replace')
        meta, body = parse_frontmatter(content)
        yield {
            'slug': path.stem,
            'path': rel,
            'category': category,
            'content': content,
            'body': body,
            'meta': meta,
            'title': meta.get('title', path.stem),
            'tags': meta.get('tags', []),
            'sources': meta.get('sources', []),
        }


def page_slugs(include_indexes=False):
    return {page['slug'] for page in iter_wiki_pages(include_indexes=include_indexes)}


def tokenize(text):
    return [token.lower() for token in TOKEN_RE.findall(text)]