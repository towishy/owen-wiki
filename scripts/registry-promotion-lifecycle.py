"""Maintain a registry promotion lifecycle from the action queue."""
import argparse
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


def save_state(items):
    payload = {
        'updated': date.today().isoformat(),
        'items': items,
        'status_counts': status_counts(items),
    }
    STATE_JSON.parent.mkdir(parents=True, exist_ok=True)
    STATE_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    OUT_MD.write_text(render_markdown(items), encoding='utf-8')
    return payload


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
            'group': candidate.get('group', ''),
            'group_size': candidate.get('group_size', 1),
            'last_seen': today,
        })
        recommendation, reason = recommend_status(item)
        item['recommended_status'] = recommendation
        item['recommendation_reason'] = reason
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
            if item.get('status', DEFAULT_STATUS) == DEFAULT_STATUS:
                item['status'] = 'deferred'
                item['decision_note'] = item.get('decision_note') or 'action queue dedupe/score update로 현재 Top 후보에서 제외됨'
            merged.append(item)
    return sorted(merged, key=lambda item: (STATUS_ORDER.index(item.get('status', DEFAULT_STATUS)) if item.get('status', DEFAULT_STATUS) in STATUS_ORDER else 99, item.get('queue_rank', 999), -item.get('score', 0)))


def recommend_status(item):
    signals = item.get('signals', '').lower()
    score = int(item.get('score') or 0)
    sources = int(item.get('sources') or 0)
    group_size = int(item.get('group_size') or 1)
    if item.get('target_summary'):
        return 'promoted', 'target_summary가 기록되어 승격 완료 후보'
    if 'generic-outputs' in signals or 'generic-_templates' in signals or 'generic-_moc' in signals:
        return 'deferred', 'generic registry 성격이 강해 직접 summary 승격 우선순위 낮음'
    if 'customer' in signals and (score >= 15 or sources >= 20):
        return 'sampled', '고객 신호와 충분한 source 수가 있어 대표 원본 샘플링 권장'
    if any(token in signals for token in ('prod/sentinel', 'prod/entra', 'prod/mde', 'prod/purview', 'prod/security-copilot')) and sources >= 10:
        return 'sampled', '제품 신호와 source 수가 충분해 curated summary 후보'
    if group_size >= 5 and sources >= 40:
        return 'sampled', '대형 part 그룹 대표 후보라 샘플링 후 하위 분할 판단 필요'
    if score <= 3:
        return 'deferred', '점수가 낮아 상위 큐레이션 후보에서 후순위'
    return 'candidate', '추가 신호 확인 필요'


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
        '| Rank | Page | Status | Recommended | Score | Sources | Group | Signals | Target summary | Decision note |',
        '|---:|---|---|---|---:|---:|---:|---|---|---|',
    ]
    for item in items[:50]:
        page = item.get('page', '')
        target = item.get('target_summary', '') or '-'
        note = item.get('decision_note', '') or '-'
        rank = item.get('queue_rank', '-')
        lines.append(
            f"| {rank} | [[{page}]] | `{item.get('status', DEFAULT_STATUS)}` | `{item.get('recommended_status', '-')}` | {item.get('score', 0)} | {item.get('sources', 0)} | {item.get('group_size', 1)} | {item.get('signals', '')} | {target} | {note} |"
        )
    lines += [
        '',
        '## Recommendation Rules',
        '',
        '- `sampled`: 고객/제품 신호가 강하거나 대형 part 그룹 대표 후보인 경우.',
        '- `deferred`: outputs/templates/MOC 등 generic registry 성격이 강하거나 점수가 낮은 경우.',
        '- `promoted`: `target_summary`가 기록된 경우.',
        '- `candidate`: 자동 추천 근거가 약해 사람 검토가 필요한 경우.',
        '',
        '## Lifecycle Rules',
        '',
        '1. `candidate`: Action Queue Top 후보로 자동 등록한다.',
        '2. `sampled`: sources 중 대표 파일 3~5개를 검토한다.',
        '3. `promoted`: curated summary 또는 synthesis를 만들고 `target_summary`에 위키링크를 기록한다.',
        '4. `deferred`: 중복·저가치·시기상조 후보는 보류하고 `decision_note`를 남긴다.',
        '5. `rejected`: PII/부적합/중복 원본처럼 재검토 가치가 낮은 경우에만 사용한다.',
        '',
        '## CLI Usage',
        '',
        '```bash',
        'python scripts/registry-promotion-lifecycle.py --set PAGE sampled --note "대표 sources 5개 샘플링 시작"',
        'python scripts/registry-promotion-lifecycle.py --set PAGE promoted --target-summary "[[new-summary]]"',
        '```',
        '',
    ]
    return '\n'.join(lines)


def apply_status_update(items, page, status, note='', target_summary='', owner=''):
    if status not in STATUS_ORDER:
        raise SystemExit(f'Invalid status: {status}. Expected one of: {", ".join(STATUS_ORDER)}')
    for item in items:
        if item.get('page') == page:
            item['status'] = status
            item['updated'] = date.today().isoformat()
            if note:
                item['decision_note'] = note
            if target_summary:
                item['target_summary'] = target_summary
            if owner:
                item['owner'] = owner
            return item
    raise SystemExit(f'Page not found in lifecycle: {page}')


def main():
    parser = argparse.ArgumentParser(description='Maintain registry promotion lifecycle state.')
    parser.add_argument('--set', dest='page', help='Page slug to update')
    parser.add_argument('status', nargs='?', help='New status: candidate/sampled/promoted/deferred/rejected')
    parser.add_argument('--note', default='', help='Decision note')
    parser.add_argument('--target-summary', default='', help='Target summary wikilink for promoted items')
    parser.add_argument('--owner', default='', help='Owner or reviewer')
    args = parser.parse_args()

    queue = load_json(ACTION_QUEUE_JSON, {'registry_promotion_candidates': []})
    state = load_json(STATE_JSON, {'items': []})
    items = merge_candidates(queue, state)
    if args.page:
        if not args.status:
            raise SystemExit('--set requires a status argument')
        updated = apply_status_update(items, args.page, args.status, args.note, args.target_summary, args.owner)
        print(f"Updated: {updated['page']} -> {updated['status']}")
    save_state(items)
    print(f'Lifecycle items: {len(items)}')
    print(f'State: {STATE_JSON}')
    print(f'Report: {OUT_MD}')


if __name__ == '__main__':
    main()