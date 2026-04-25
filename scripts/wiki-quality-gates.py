"""Strict quality gates for CI and local wiki maintenance."""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCRIPTS = ROOT / 'scripts'
WIKI_SUMMARIES = ROOT / 'wiki' / 'summaries'


def run_script(name):
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / name)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        timeout=120,
    )
    return result.returncode, result.stdout + result.stderr


def fail(message, details=''):
    print(f'[FAIL] {message}')
    if details:
        print(details.strip())
    return False


def pass_gate(message):
    print(f'[OK] {message}')
    return True


def check_output(name, pattern, ok_value='0'):
    code, output = run_script(name)
    if code != 0:
        return fail(f'{name} exited with {code}', output)
    match = re.search(pattern, output)
    if not match:
        return fail(f'{name} output did not match expected pattern', output)
    value = match.group(1)
    if value != ok_value:
        return fail(f'{name} gate expected {ok_value}, got {value}', output)
    return pass_gate(f'{name}: {pattern} == {ok_value}')


def check_remaining_registry_parent_links():
    offenders = []
    for path in sorted(WIKI_SUMMARIES.glob('remaining-raw-*.md')):
        if path.name == 'remaining-raw-source-registry-hub.md':
            continue
        text = path.read_text(encoding='utf-8', errors='replace')
        if '[[remaining-raw-source-registry-hub]]' not in text:
            offenders.append(path.relative_to(ROOT).as_posix())
    if offenders:
        return fail('remaining raw registry pages must link to parent hub', '\n'.join(offenders[:50]))
    return pass_gate('remaining raw registry parent hub links')


def main():
    gates = [
        check_output('scan-broken-links.py', r'Truly broken:\s+(\d+) occurrences'),
        check_output('find-orphans.py', r'Orphan pages \(0 inbound links\):\s+(\d+)'),
        check_output('check-tags.py', r'Tag prefix compliance:\s+\d+ OK,\s+(\d+) non-compliant'),
        check_output('identify-stubs.py', r'Stubs found:\s+(\d+)\s+/'),
        check_remaining_registry_parent_links(),
    ]
    if not all(gates):
        sys.exit(1)
    print('All wiki quality gates passed')


if __name__ == '__main__':
    main()
