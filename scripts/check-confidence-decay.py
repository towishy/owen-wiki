"""Detect aging/stale wiki pages based on last_confirmed/updated dates.

AGENTS.md v1.4.0 — Confidence & Lifecycle 라이프사이클 점검.

규칙:
- last_confirmed (없으면 updated) 기준
- 90일 경과 → 'aging' 권장
- 180일 경과 또는 stale_after 초과 → 'stale' 권장
- superseded_by 보유 페이지는 자동 stale

사용:
    .venv/bin/python scripts/check-confidence-decay.py            # 보고만
    .venv/bin/python scripts/check-confidence-decay.py --apply    # 태그 자동 부여
"""
import os
import re
import sys
from datetime import date, datetime, timedelta

WIKI_ROOT = os.path.join(os.path.dirname(__file__), '..', 'wiki')
TODAY = date.today()
AGING_DAYS = 90
STALE_DAYS = 180

apply_changes = '--apply' in sys.argv


def parse_date(s):
    if not s:
        return None
    s = s.strip().strip('"').strip("'")
    if not s:
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except ValueError:
        return None


def parse_frontmatter(content):
    m = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not m:
        return {}, 0
    fm_text = m.group(1)
    fm = {}
    for line in fm_text.split('\n'):
        if ':' not in line:
            continue
        k, _, v = line.partition(':')
        fm[k.strip()] = v.strip()
    return fm, m.end()


def classify(fm):
    """Return ('ok'|'aging'|'stale', reason)."""
    if fm.get('superseded_by') and fm['superseded_by'] not in ('""', "''", ''):
        return 'stale', 'superseded_by 보유'

    stale_after = parse_date(fm.get('stale_after', ''))
    if stale_after and TODAY >= stale_after:
        return 'stale', f'stale_after 초과 ({stale_after})'

    base_date = parse_date(fm.get('last_confirmed', '')) or parse_date(fm.get('updated', ''))
    if not base_date:
        return 'ok', 'no date'

    age = (TODAY - base_date).days
    if age >= STALE_DAYS:
        return 'stale', f'{age}일 경과'
    if age >= AGING_DAYS:
        return 'aging', f'{age}일 경과'
    return 'ok', f'{age}일'


def get_tags(fm):
    raw = fm.get('tags', '[]')
    m = re.search(r'\[([^\]]*)\]', raw)
    if not m:
        return []
    return [t.strip().strip('"').strip("'") for t in m.group(1).split(',') if t.strip()]


def add_tag(content, fm_end, new_tag):
    fm_text = content[:fm_end]
    rest = content[fm_end:]
    tags_match = re.search(r'(tags:\s*\[)([^\]]*)(\])', fm_text)
    if not tags_match:
        return content
    existing = tags_match.group(2)
    tags = [t.strip().strip('"').strip("'") for t in existing.split(',') if t.strip()]
    if new_tag in tags:
        return content
    # remove conflicting lifecycle tag
    tags = [t for t in tags if t not in ('aging', 'stale')]
    tags.append(new_tag)
    new_inside = ', '.join(tags)
    new_fm = fm_text[:tags_match.start(2)] + new_inside + fm_text[tags_match.end(2):]
    return new_fm + rest


def main():
    counts = {'ok': 0, 'aging': 0, 'stale': 0, 'no_fm': 0}
    findings = []

    for root, dirs, files in os.walk(WIKI_ROOT):
        if 'ontology' in root:
            continue
        for f in files:
            if not f.endswith('.md') or f in ('_index.md', 'README.md'):
                continue
            fp = os.path.join(root, f)
            with open(fp, 'r', encoding='utf-8') as fh:
                content = fh.read()
            fm, fm_end = parse_frontmatter(content)
            if not fm:
                counts['no_fm'] += 1
                continue
            status, reason = classify(fm)
            counts[status] += 1
            if status in ('aging', 'stale'):
                rel = os.path.relpath(fp, WIKI_ROOT)
                findings.append((status, rel, reason))
                tags = get_tags(fm)
                if status not in tags and apply_changes:
                    new_content = add_tag(content, fm_end, status)
                    if new_content != content:
                        with open(fp, 'w', encoding='utf-8') as fh:
                            fh.write(new_content)

    print('=== Confidence Decay Report ===')
    print(f'  OK      : {counts["ok"]}')
    print(f'  Aging   : {counts["aging"]} (90+ days)')
    print(f'  Stale   : {counts["stale"]} (180+ days or superseded)')
    print(f'  No FM   : {counts["no_fm"]}')
    print()
    if findings:
        print('## Findings')
        for status, rel, reason in sorted(findings, key=lambda x: (x[0], x[1])):
            print(f'  [{status:5s}] {rel:60s} — {reason}')
    if apply_changes:
        print()
        print(f'✓ Applied tag updates to {len(findings)} files.')
    else:
        print()
        print('Run with --apply to auto-add aging/stale tags.')


if __name__ == '__main__':
    main()
