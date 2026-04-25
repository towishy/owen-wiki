"""Apply scripts/tag-aliases.yml to wiki page frontmatter tags."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
WIKI_ROOT = ROOT / 'wiki'
ALIASES_FILE = ROOT / 'scripts' / 'tag-aliases.yml'
FM_RE = re.compile(r'^---\n(.*?)\n---', re.DOTALL)
TAGS_RE = re.compile(r'^tags:\s*\[([^\]]*)\]', re.MULTILINE)


def load_aliases():
    aliases = {}
    current = None
    for line in ALIASES_FILE.read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        if not line.startswith(' ') and ':' in line:
            current = line.split(':', 1)[0].strip()
            aliases[current] = current
        elif current and line.strip().startswith('- '):
            aliases[line.strip()[2:].strip()] = current
    return aliases


def parse_tags(raw):
    return [tag.strip().strip('"').strip("'") for tag in raw.split(',') if tag.strip()]


def render_tags(tags):
    return ', '.join(tags)


def process_file(path, aliases, dry_run=False):
    text = path.read_text(encoding='utf-8', errors='replace')
    fm_match = FM_RE.match(text)
    if not fm_match:
        return False, []
    fm_text = fm_match.group(1)
    tags_match = TAGS_RE.search(fm_text)
    if not tags_match:
        return False, []
    old_tags = parse_tags(tags_match.group(1))
    new_tags = []
    changes = []
    seen = set()
    for tag in old_tags:
        new_tag = aliases.get(tag, tag)
        if new_tag != tag:
            changes.append(f'{tag}->{new_tag}')
        if new_tag not in seen:
            new_tags.append(new_tag)
            seen.add(new_tag)
    if new_tags == old_tags:
        return False, []
    new_fm = fm_text[:tags_match.start(1)] + render_tags(new_tags) + fm_text[tags_match.end(1):]
    new_text = text[:fm_match.start(1)] + new_fm + text[fm_match.end(1):]
    if not dry_run:
        path.write_text(new_text, encoding='utf-8')
    return True, changes


def main():
    dry_run = '--dry-run' in sys.argv
    aliases = load_aliases()
    changed = 0
    for path in sorted(WIKI_ROOT.rglob('*.md')):
        if path.name in ('_index.md', 'README.md') or 'ontology' in path.parts:
            continue
        updated, changes = process_file(path, aliases, dry_run=dry_run)
        if updated:
            changed += 1
            rel = path.relative_to(ROOT).as_posix()
            marker = '[DRY]' if dry_run else '[OK]'
            print(f'{marker} {rel}: {", ".join(changes)}')
    print(f'{"DRY-RUN" if dry_run else "DONE"}: {changed} files changed')


if __name__ == '__main__':
    main()
