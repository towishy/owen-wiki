"""Maintain a registry promotion lifecycle from the action queue."""
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUTPUTS_ROOT = ROOT / 'outputs'
ACTION_QUEUE_JSON = OUTPUTS_ROOT / 'drafts' / 'wiki-action-queue.json'
STATE_JSON = OUTPUTS_ROOT / 'drafts' / 'registry-promotion-lifecycle.json'
OUT_MD = OUTPUTS_ROOT / 'drafts' / 'registry-promotion-lifecycle.md'

DEFAULT_STATUS = 'candidate'
STATUS_ORDER = ['candidate', 'sampled', 'promoted', 'deferred', 'rejected']


def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8'))


def status_counts(items):
    counts = {status: 0 for status in STATUS_ORDER}
    for item in items:
        counts[item.get('status', DEFAULT_STATUS)] = counts.get(item.get('status', DEFAULT_STATUS), 0) + 1
    return counts


def merge_candidates(queue, state):
    existing = {item['page']: item for item in state.get('items', []) if 'page' in item}
    today = date.today().isoformat()
    merged = []
    for rank, candidate in enumerate(queue.get('registry_promotion_candidates', []), 1):
        page = candidate['page']
        item = dict(existing.get(page, {}))
        item.update({
            'page': page,
            'path': candidate.get('path'),
            'queue_rank': rank,
            'score': candidate.get('score', 0),
            'sources': candidate.get('sources', 0),
            'signals': candidate.get('signals', ''),
            'last_seen': today,
        })
        item.setdefault('status', DEFAULT_STATUS)
        item.setdefault('owner', '')
        item.setdefault('decision_note', '')
        item.setdefault('target_summary', '')
        item.setdefault('created', today)
        merged.append(item)

    known_pages = {item['page'] for item in merged}
    for page, item in existing.items():
        if page not in known_pages:
            item = dict(item)
            item.setdefault('status', 'deferred')
            merged.append(item)
    return sorted(merged, key=lambda item: (STATUS_ORDER.index(item.get('status', DEFAULT_STATUS)) if item.get('status', DEFAULT_STATUS) in STATUS_ORDER else 99, item.get('queue_rank', 999), -item.get('score', 0)))


def render_markdown(items):
    today = date.today().isoformat()
    counts = status_counts(items)
    lines = [
        '---',
        'title: "Registry Promotion Lifecycle"',
        'type: report',
        f'updated: {today}',
        '---',
        '',
        f'# Registry Promotion Lifecycle — {today}',
        '',
        '> Source registry는 raw coverage 증명 레이어다. 이 파일은 후보를 sampled/promoted/deferred/rejected 상태로 추적해 curated summary 승격 흐름을 관리한다.',
        '',
        '## Status Summary',
        '',
        '| Status | Count | Meaning |',
        '|---|---:|---|',
        f"| `candidate` | {counts.get('candidate', 0)} | action queue에서 새로 선별된 승격 후보 |",
        f"| `sampled` | {counts.get('sampled', 0)} | 원본 샘플링 중 |",
        f"| `promoted` | {counts.get('promoted', 0)} | curated summary/entity/concept/synthesis로 승격 완료 |",
        f"| `deferred` | {counts.get('deferred', 0)} | 가치 낮음 또는 중복으로 보류 |",
        f"| `rejected` | {counts.get('rejected', 0)} | 수집 제외 결정 |",
        '',
        '## Promotion Board',
        '',
        '| Rank | Page | Status | Score | Sources | Signals | Target summary | Decision note |',
        '|---:|---|---|---:|---:|---|---|---|',
    ]
    for item in items[:50]:
        page = item.get('page', '')
        target = item.get('target_summary', '') or '-'
        note = item.get('decision_note', '') or '-'
        rank = item.get('queue_rank', '-')
        lines.append(
            f"| {rank} | [[{page}]] | `{item.get('status', DEFAULT_STATUS)}` | {item.get('score', 0)} | {item.get('sources', 0)} | {item.get('signals', '')} | {target} | {note} |"
        )
    lines += [
        '',
        '## Lifecycle Rules',
        '',
        '1. `candidate`: Action Queue Top 후보로 자동 등록한다.',
        '2. `sampled`: sources 중 대표 파일 3~5개를 검토한다.',
        '3. `promoted`: curated summary 또는 synthesis를 만들고 `target_summary`에 위키링크를 기록한다.',
        '4. `deferred`: 중복·저가치·시기상조 후보는 보류하고 `decision_note`를 남긴다.',
        '5. `rejected`: PII/부적합/중복 원본처럼 재검토 가치가 낮은 경우에만 사용한다.',
        '',
    ]
    return '\n'.join(lines)


def main():
    queue = load_json(ACTION_QUEUE_JSON, {'registry_promotion_candidates': []})
    state = load_json(STATE_JSON, {'items': []})
    items = merge_candidates(queue, state)
    payload = {
        'updated': date.today().isoformat(),
        'items': items,
        'status_counts': status_counts(items),
    }
    STATE_JSON.parent.mkdir(parents=True, exist_ok=True)
    STATE_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    OUT_MD.write_text(render_markdown(items), encoding='utf-8')
    print(f'Lifecycle items: {len(items)}')
    print(f'State: {STATE_JSON}')
    print(f'Report: {OUT_MD}')


if __name__ == '__main__':
    main()