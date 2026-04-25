"""Weekly gap analysis — orphans, broken links, stubs, decay, action queue, ops dashboard 종합 보고서.

기존 스크립트 결과를 묶어 outputs/drafts/weekly-gaps-YYYY-MM-DD.md 생성.

사용:
  python scripts/weekly-gap-report.py
"""
import subprocess
import sys
from pathlib import Path
from datetime import date

ROOT = Path(__file__).parent.parent
SCRIPTS = ROOT / 'scripts'
OUT_DIR = ROOT / 'outputs' / 'drafts'
TODAY = date.today().isoformat()
OUT_PATH = OUT_DIR / f'weekly-gaps-{TODAY}.md'


def run(name, *args):
    cmd = [sys.executable, str(SCRIPTS / name), *args]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                           timeout=120, encoding='utf-8', errors='replace')
        return r.stdout + ('\n[stderr]\n' + r.stderr if r.stderr else '')
    except Exception as e:
        return f'[ERROR] {name}: {e}'


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sections = []
    sections.append(('## 1. Orphan Pages', run('find-orphans.py')))
    sections.append(('## 2. Broken Wikilinks', run('scan-broken-links.py')))
    sections.append(('## 3. Confidence Decay (aging/stale)', run('check-confidence-decay.py')))
    sections.append(('## 4. Stub Pages', run('identify-stubs.py')))
    sections.append(('## 5. Ontology Health', run('check-ontology.py')))
    sections.append(('## 6. Tag Drift', run('check-tags.py')))
    sections.append(('## 7. Raw → Wiki 변환율', run('build-raw-to-wiki-map.py')))
    sections.append(('## 8. Ontology Sidecar', run('build-ontology-sidecar.py')))
    sections.append(('## 9. Action Queue', run('wiki-action-queue.py')))
    sections.append(('## 10. Registry Promotion Lifecycle', run('registry-promotion-lifecycle.py')))
    sections.append(('## 11. Ontology Relation Quality', run('check-ontology-relations.py')))
    sections.append(('## 12. Operations Dashboard', run('wiki-ops-dashboard.py')))

    lines = [
        '---', f'title: "Weekly Gap Report — {TODAY}"', 'type: report',
        f'updated: {TODAY}', '---', '',
        f'# Weekly Gap Report — {TODAY}',
        '',
        '> AGENTS.md Lint 워크플로 자동 실행 결과. 다음 ingest/lint 우선순위 결정.',
        '',
    ]
    for header, output in sections:
        lines.append(header)
        lines.append('')
        lines.append('```')
        lines.append(output.rstrip())
        lines.append('```')
        lines.append('')
    OUT_PATH.write_text('\n'.join(lines), encoding='utf-8')
    print(f'Report written: {OUT_PATH}')


if __name__ == '__main__':
    main()
