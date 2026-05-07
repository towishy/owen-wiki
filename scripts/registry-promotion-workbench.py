"""Build review packets for registry promotion candidates."""
import json
from datetime import date

from wiki_utils import OUTPUTS_ROOT, ROOT, md_cell

ACTION_QUEUE_JSON = OUTPUTS_ROOT / 'wiki-ops' / 'wiki-action-queue.json'
LIFECYCLE_JSON = OUTPUTS_ROOT / 'wiki-ops' / 'registry-promotion-lifecycle.json'
OUT_JSON = OUTPUTS_ROOT / 'wiki-ops' / 'registry-promotion-workbench.json'
OUT_MD = OUTPUTS_ROOT / 'wiki-ops' / 'registry-promotion-workbench.md'


def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8'))


def sample_sources(path, limit=5):
    page_path = ROOT / path
    if not page_path.exists():
        return []
    sources = []
    in_sources = False
    for line in page_path.read_text(encoding='utf-8', errors='replace').splitlines():
        if line.strip() == 'sources:':
            in_sources = True
            continue
        if in_sources and line.startswith('  - '):
            sources.append(line[4:].strip().strip('"').strip("'"))
            if len(sources) >= limit:
                break
        elif in_sources and line and not line.startswith(' '):
            break
    return sources


def recommendation(item):
    status = item.get('recommended_status') or item.get('status') or 'candidate'
    if status == 'sampled':
        return '대표 source 3~5개를 읽고 curated summary 가치 판단'
    if status == 'deferred':
        return '중복·generic registry 여부 확인 후 보류 사유 기록'
    if status == 'promoted':
        return 'target_summary 품질 확인 및 registry backlink 유지'
    return '제품/고객/워크숍 신호를 확인해 sampled 또는 deferred로 분류'


def build_payload():
    queue = load_json(ACTION_QUEUE_JSON, {'registry_promotion_candidates': []})
    lifecycle = load_json(LIFECYCLE_JSON, {'items': []})
    lifecycle_by_page = {item.get('page'): item for item in lifecycle.get('items', [])}
    packets = []
    for rank, candidate in enumerate(queue.get('registry_promotion_candidates', [])[:20], 1):
        merged = dict(candidate)
        merged.update(lifecycle_by_page.get(candidate.get('page'), {}))
        merged['rank'] = rank
        merged['sample_sources'] = sample_sources(candidate.get('path', ''), 5)
        merged['next_action'] = recommendation(merged)
        packets.append(merged)
    return {'updated': date.today().isoformat(), 'packets': packets}


def render(payload):
    lines = [
        '---', 'title: "Registry Promotion Workbench"', 'type: report', f"updated: {payload['updated']}", '---', '',
        f"# Registry Promotion Workbench — {payload['updated']}", '',
        '> Top registry candidates를 실제 검토 가능한 packet으로 압축한다.', '',
        '| Rank | Page | Status | Score | Sources | Signals | Next action |',
        '|---:|---|---|---:|---:|---|---|',
    ]
    for item in payload['packets']:
        lines.append(f"| {item.get('rank')} | [[{md_cell(item.get('page', ''))}]] | `{item.get('status', 'candidate')}` | {item.get('score', 0)} | {item.get('sources', 0)} | {md_cell(item.get('signals', ''))} | {item.get('next_action')} |")
    if not payload['packets']:
        lines.append('| - | - | - | - | - | - | 후보 없음 |')
    lines += ['', '## Review Packets', '']
    for item in payload['packets'][:10]:
        lines += [
            f"### {item.get('rank')}. {item.get('page')}", '',
            f"- Path: `{item.get('path', '-')}`",
            f"- Recommended: `{item.get('recommended_status', item.get('status', 'candidate'))}` — {item.get('recommendation_reason', '-')}",
            f"- Next action: {item.get('next_action')}",
            '- Sample sources:',
        ]
        for source in item.get('sample_sources', []):
            lines.append(f'  - `{source}`')
        if not item.get('sample_sources'):
            lines.append('  - 없음')
        lines.append('')
    return '\n'.join(lines)


def main():
    payload = build_payload()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    OUT_MD.write_text(render(payload), encoding='utf-8')
    print(f"Workbench packets: {len(payload['packets'])}")
    print(f'Report: {OUT_MD}')


if __name__ == '__main__':
    main()