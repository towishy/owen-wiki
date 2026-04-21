"""PII / 민감정보 사전 점검 스크립트.

AGENTS.md v1.4.0 — Ingest 0단계.

탐지 대상:
- 이메일 주소
- IPv4 / IPv6 주소
- Bearer 토큰 / JWT
- GUID / UUID
- 한국 주민등록번호
- 전화번호 (한국 형식)
- AWS Access Key, Azure SAS Token

사용:
    .venv/bin/python scripts/sanitize-ingest.py <파일1> [<파일2> ...]
    .venv/bin/python scripts/sanitize-ingest.py raw/articles/new.md

옵션:
    --mask  발견 항목을 [MASKED-<TYPE>] 로 치환한 사본 출력 (.sanitized.md)
    --quiet 발견 시에만 출력
"""
import os
import re
import sys

PATTERNS = {
    'EMAIL': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'),
    'IPV4': re.compile(r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\b'),
    'IPV6': re.compile(r'\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\b'),
    'GUID': re.compile(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b'),
    'JWT': re.compile(r'\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b'),
    'BEARER': re.compile(r'(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{20,}'),
    'AWS_KEY': re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
    'KR_RRN': re.compile(r'\b\d{6}-[1-4]\d{6}\b'),
    'KR_PHONE': re.compile(r'\b01[0-9]-?\d{3,4}-?\d{4}\b'),
    'AZURE_SAS': re.compile(r'\bsig=[A-Za-z0-9%]{30,}'),
}

# 안전한 컨텍스트 (Microsoft 공식 예시 IP, 문서 도메인 등)
WHITELIST = {
    'EMAIL': re.compile(r'@(?:microsoft|example|contoso|fabrikam|githubusercontent|github)\.(?:com|io)'),
    'IPV4': re.compile(r'^(?:0\.0\.0\.0|127\.0\.0\.1|255\.255\.255\.255|192\.168\.|10\.|172\.(?:1[6-9]|2\d|3[01])\.|169\.254\.)'),
}

mask_mode = '--mask' in sys.argv
quiet_mode = '--quiet' in sys.argv
files = [a for a in sys.argv[1:] if not a.startswith('--')]

if not files:
    print(__doc__)
    sys.exit(1)


def is_whitelisted(kind, value):
    wl = WHITELIST.get(kind)
    if not wl:
        return False
    return bool(wl.search(value))


def scan_file(path):
    findings = []
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as fh:
            content = fh.read()
    except Exception as e:
        print(f'ERROR reading {path}: {e}', file=sys.stderr)
        return None, []

    for kind, pat in PATTERNS.items():
        for m in pat.finditer(content):
            val = m.group(0)
            if is_whitelisted(kind, val):
                continue
            line_no = content[:m.start()].count('\n') + 1
            findings.append((kind, line_no, val))

    if mask_mode and findings:
        masked = content
        # apply substitutions per kind in reverse to preserve indices
        for kind, pat in PATTERNS.items():
            def repl(m):
                if is_whitelisted(kind, m.group(0)):
                    return m.group(0)
                return f'[MASKED-{kind}]'
            masked = pat.sub(repl, masked)
        out_path = path + '.sanitized.md'
        with open(out_path, 'w', encoding='utf-8') as fh:
            fh.write(masked)
        return out_path, findings

    return None, findings


def main():
    total = 0
    flagged = 0
    for f in files:
        if not os.path.exists(f):
            print(f'SKIP (not found): {f}', file=sys.stderr)
            continue
        out, findings = scan_file(f)
        total += 1
        if findings:
            flagged += 1
            print(f'\n⚠️  {f}  — {len(findings)} 건 발견')
            counts = {}
            for kind, _, _ in findings:
                counts[kind] = counts.get(kind, 0) + 1
            for kind, cnt in sorted(counts.items()):
                print(f'   {kind:10s} : {cnt}')
            if not quiet_mode:
                for kind, ln, val in findings[:20]:
                    show = val if len(val) < 60 else val[:57] + '...'
                    print(f'     L{ln:5d} [{kind:10s}] {show}')
                if len(findings) > 20:
                    print(f'     ... and {len(findings) - 20} more')
            if out:
                print(f'   → 마스킹 사본: {out}')
        elif not quiet_mode:
            print(f'✓ {f}  — clean')

    print(f'\n=== Summary: {flagged}/{total} files flagged ===')
    sys.exit(1 if flagged else 0)


if __name__ == '__main__':
    main()
