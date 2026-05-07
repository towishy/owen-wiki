"""Wiki repository statistics.

Default output remains a human-readable console report. Use `--json` for a
machine-readable payload and `--write-ops` to publish canonical repo metrics to
`outputs/wiki-ops/repo-metrics.{json,md}`.
"""
import argparse
import json
import os
import re
import subprocess
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT_JSON = ROOT / 'outputs' / 'wiki-ops' / 'repo-metrics.json'
OUT_MD = ROOT / 'outputs' / 'wiki-ops' / 'repo-metrics.md'

CATEGORIES = ['entities', 'concepts', 'summaries', 'comparisons', 'synthesis']
LINK_PAT = re.compile(r'\[\[([^\[\]]+?)\]\]')


def collect_metrics():
    os.chdir(ROOT)
    cat_counts = {}
    total_wiki = 0
    for category in CATEGORIES:
        path = ROOT / 'wiki' / category
        files = [name for name in os.listdir(path) if name.endswith('.md') and name not in ('_index.md', 'README.md')]
        cat_counts[category] = len(files)
        total_wiki += len(files)

    ont_files = [name for name in os.listdir(ROOT / 'wiki' / 'ontology') if name.endswith('.md') and name not in ('_index.md', 'README.md')]
    ont_count = len(ont_files)

    all_tags = Counter()
    prod_tags = Counter()
    customer_tags = Counter()
    topic_tags = Counter()
    type_tags = Counter()
    series_tags = Counter()
    page_count_with_tags = 0

    conf_buckets = {'0.95-1.0': 0, '0.80-0.94': 0, '0.65-0.79': 0, '0.40-0.64': 0, '<0.40': 0, 'unset': 0}
    superseded_count = 0
    aging_count = 0
    stale_count = 0

    for root, _, files in os.walk(ROOT / 'wiki'):
        if 'ontology' in Path(root).parts:
            continue
        for filename in files:
            if not filename.endswith('.md') or filename in ('_index.md', 'README.md'):
                continue
            content = (Path(root) / filename).read_text(encoding='utf-8', errors='replace')
            match = re.search(r'tags:\s*\[([^\]]*)\]', content)
            if match:
                page_count_with_tags += 1
                tags = [tag.strip().strip('"').strip("'") for tag in match.group(1).split(',') if tag.strip()]
                for tag in tags:
                    all_tags[tag] += 1
                    if tag.startswith('prod/'):
                        prod_tags[tag] += 1
                    elif tag.startswith('customer/'):
                        customer_tags[tag] += 1
                    elif tag.startswith('topic/'):
                        topic_tags[tag] += 1
                    elif tag.startswith('type/'):
                        type_tags[tag] += 1
                    elif tag.startswith('series/'):
                        series_tags[tag] += 1
                if 'aging' in tags:
                    aging_count += 1
                if 'stale' in tags:
                    stale_count += 1

            confidence_match = re.search(r'^confidence:\s*([0-9.]+)', content, re.MULTILINE)
            if confidence_match:
                try:
                    value = float(confidence_match.group(1))
                    if value >= 0.95:
                        conf_buckets['0.95-1.0'] += 1
                    elif value >= 0.80:
                        conf_buckets['0.80-0.94'] += 1
                    elif value >= 0.65:
                        conf_buckets['0.65-0.79'] += 1
                    elif value >= 0.40:
                        conf_buckets['0.40-0.64'] += 1
                    else:
                        conf_buckets['<0.40'] += 1
                except ValueError:
                    conf_buckets['unset'] += 1
            else:
                conf_buckets['unset'] += 1

            superseded_match = re.search(r'^superseded_by:\s*(\S.*)', content, re.MULTILINE)
            if superseded_match and superseded_match.group(1).strip() not in ('""', "''", '[]'):
                superseded_count += 1

    total_links = 0
    total_words = 0
    total_lines = 0
    for root, _, files in os.walk(ROOT / 'wiki'):
        for filename in files:
            if not filename.endswith('.md'):
                continue
            lines = (Path(root) / filename).read_text(encoding='utf-8', errors='replace').splitlines()
            text = '\n'.join(lines)
            total_links += len(LINK_PAT.findall(text))
            total_lines += len(lines)
            total_words += sum(len(line.split()) for line in lines)

    raw_count = 0
    raw_size = 0
    for root, _, files in os.walk(ROOT / 'raw'):
        for filename in files:
            raw_count += 1
            try:
                raw_size += os.path.getsize(Path(root) / filename)
            except OSError:
                pass

    result = subprocess.run(['git', 'log', '--oneline'], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    commit_count = len(result.stdout.strip().split('\n')) if result.stdout and result.stdout.strip() else 0

    tag_groups = {
        'prod': {'unique': len(prod_tags), 'uses': sum(prod_tags.values()), 'top': prod_tags.most_common(30)},
        'customer': {'unique': len(customer_tags), 'uses': sum(customer_tags.values()), 'top': customer_tags.most_common(40)},
        'topic': {'unique': len(topic_tags), 'uses': sum(topic_tags.values()), 'top': topic_tags.most_common(20)},
        'type': {'unique': len(type_tags), 'uses': sum(type_tags.values())},
        'series': {'unique': len(series_tags), 'uses': sum(series_tags.values())},
    }
    pages_total = total_wiki + ont_count
    return {
        'updated': date.today().isoformat(),
        'pages': {'categories': cat_counts, 'ontology': ont_count, 'total': pages_total},
        'content': {
            'total_lines': total_lines,
            'total_words': total_words,
            'wikilinks': total_links,
            'avg_links_per_page': round(total_links / pages_total, 1) if pages_total else 0,
        },
        'tags': {'pages_with_tags': page_count_with_tags, 'unique': len(all_tags), 'groups': tag_groups},
        'confidence': conf_buckets,
        'lifecycle': {'superseded': superseded_count, 'aging_tag': aging_count, 'stale_tag': stale_count},
        'raw_sources': {'files': raw_count, 'bytes': raw_size, 'size_gb': round(raw_size / (1024**3), 1)},
        'git': {'commits': commit_count},
    }


def render_console(metrics):
    lines = ['=== WIKI REPOSITORY STATISTICS ===', '', '## Pages']
    for category in CATEGORIES:
        lines.append(f"  {category:15s}: {metrics['pages']['categories'][category]:>4d}")
    lines.append(f"  {'ontology':15s}: {metrics['pages']['ontology']:>4d}")
    lines.append(f"  {'-' * 15:15s}  {'-' * 4:>4s}")
    lines.append(f"  {'TOTAL':15s}: {metrics['pages']['total']:>4d}")
    content = metrics['content']
    lines += [
        '', '## Content',
        f"  Total lines:    {content['total_lines']:>8,d}",
        f"  Total words:    {content['total_words']:>8,d}",
        f"  Wikilinks:      {content['wikilinks']:>8,d}",
        f"  Avg links/page: {content['avg_links_per_page']:.1f}",
        '', '## Tags',
        f"  Pages with tags:  {metrics['tags']['pages_with_tags']}",
        f"  Unique tags:      {metrics['tags']['unique']}",
    ]
    for group in ['prod', 'customer', 'topic', 'type', 'series']:
        data = metrics['tags']['groups'][group]
        lines.append(f"  {group + '/ tags':16s} {data['unique']:>4d} ({data['uses']} uses)")
    lines.append('')
    lines.append('## Confidence & Lifecycle (v1.4.0)')
    for bucket, count in metrics['confidence'].items():
        lines.append(f'  {bucket:12s}: {count:>4d}')
    lines += [
        f"  superseded  : {metrics['lifecycle']['superseded']}",
        f"  aging tag   : {metrics['lifecycle']['aging_tag']}",
        f"  stale tag   : {metrics['lifecycle']['stale_tag']}",
        '', '## Raw Sources',
        f"  Files:            {metrics['raw_sources']['files']:,d}",
        f"  Size:             {metrics['raw_sources']['size_gb']:.1f} GB",
        '', '## Git',
        f"  Commits:          {metrics['git']['commits']}",
        '', '## Top prod/ tags (product coverage)',
    ]
    for tag, count in metrics['tags']['groups']['prod']['top']:
        lines.append(f'  {tag:40s} {count:>3d} pages')
    lines.append('')
    lines.append('## Top topic/ tags')
    for tag, count in metrics['tags']['groups']['topic']['top']:
        lines.append(f'  {tag:40s} {count:>3d} pages')
    lines.append('')
    lines.append('## customer/ tags')
    for tag, count in metrics['tags']['groups']['customer']['top']:
        lines.append(f'  {tag:40s} {count:>3d} pages')
    return '\n'.join(lines)


def render_markdown(metrics):
    content = metrics['content']
    tags = metrics['tags']
    lines = [
        '---',
        'title: "Repository Metrics"',
        'type: report',
        f"updated: {metrics['updated']}",
        '---',
        '',
        f"# Repository Metrics - {metrics['updated']}",
        '',
        '> [!summary]',
        '> Canonical repository scale metrics generated by `scripts/wiki-stats.py --write-ops`.',
        '',
        '## Core Metrics',
        '',
        '| Metric | Value |',
        '|---|---:|',
        f"| Wiki pages | {metrics['pages']['total']} |",
        f"| Wikilinks | {content['wikilinks']} |",
        f"| Total lines | {content['total_lines']} |",
        f"| Total words | {content['total_words']} |",
        f"| Unique tags | {tags['unique']} |",
        f"| Raw source files | {metrics['raw_sources']['files']} |",
        f"| Git commits | {metrics['git']['commits']} |",
        '',
        '## Pages By Category',
        '',
        '| Category | Pages |',
        '|---|---:|',
    ]
    for category, count in metrics['pages']['categories'].items():
        lines.append(f'| `{category}` | {count} |')
    lines.append(f"| `ontology` | {metrics['pages']['ontology']} |")
    lines += ['', '## Tag Groups', '', '| Group | Unique | Uses |', '|---|---:|---:|']
    for group in ['prod', 'customer', 'topic', 'type', 'series']:
        data = tags['groups'][group]
        lines.append(f"| `{group}/` | {data['unique']} | {data['uses']} |")
    lines += ['', '## Confidence', '', '| Bucket | Pages |', '|---|---:|']
    for bucket, count in metrics['confidence'].items():
        lines.append(f'| `{bucket}` | {count} |')
    lines.append('')
    return '\n'.join(lines)


def write_ops(metrics):
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    OUT_MD.write_text(render_markdown(metrics), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description='Wiki repository statistics')
    parser.add_argument('--json', action='store_true', help='print metrics as JSON')
    parser.add_argument('--write-ops', action='store_true', help='write outputs/wiki-ops/repo-metrics.{json,md}')
    args = parser.parse_args()

    metrics = collect_metrics()
    if args.write_ops:
        write_ops(metrics)
    if args.json:
        print(json.dumps(metrics, ensure_ascii=False, indent=2))
    else:
        print(render_console(metrics))


if __name__ == '__main__':
    main()
