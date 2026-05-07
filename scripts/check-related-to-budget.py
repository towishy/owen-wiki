"""Enforce a budget for weak ontology `related-to` relations."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCRIPTS = ROOT / 'scripts'
RELATION_QUALITY_JSON = ROOT / 'outputs' / 'wiki-ops' / 'ontology-relation-quality.json'


def run_relation_report():
    subprocess.run([sys.executable, str(SCRIPTS / 'build-ontology-sidecar.py')], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(SCRIPTS / 'check-ontology-relations.py')], cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description='Check related-to budget.')
    parser.add_argument('--max', type=int, default=10, help='Maximum allowed related-to relations')
    parser.add_argument('--refresh', action='store_true', help='Regenerate ontology sidecar and relation report first')
    args = parser.parse_args()
    if args.refresh or not RELATION_QUALITY_JSON.exists():
        run_relation_report()
    payload = json.loads(RELATION_QUALITY_JSON.read_text(encoding='utf-8'))
    count = int(payload.get('weak_related_to_count', 0))
    print(f'related-to count: {count}')
    print(f'related-to budget: {args.max}')
    if count > args.max:
        print(f'[FAIL] related-to count exceeds budget by {count - args.max}')
        sys.exit(1)
    print('[OK] related-to budget passed')


if __name__ == '__main__':
    main()