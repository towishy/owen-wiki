#!/usr/bin/env python3
"""
auto-extract-triplets.py — LLM 기반 ENTITIES/RELATIONS 트리플렛 자동 추출 스켈레톤

AGENTS.md "트리플렛 추출 프로토콜" (LightRAG 차용) 구현 골격.
입력: 마크다운 파일 경로
출력: stdout에 ENTITIES/RELATIONS YAML 블록

사용법:
    python scripts/auto-extract-triplets.py <markdown-file> [--model gpt-4o]

⚠️ 이 파일은 스켈레톤이다. 실제 LLM 호출부는 사용자가 자신의 API 키로 채워야 한다.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

PROMPT_TEMPLATE = """당신은 위키 온톨로지 추출기입니다.
아래 마크다운 문서에서 5–20개의 (주체, 관계, 객체) 트리플렛을 추출하세요.

규칙:
- 모든 트리플렛은 문서의 명시적 진술에 근거해야 합니다 (일반 지식 추론 금지).
- 출력은 정확히 아래 YAML 형식을 따릅니다.
- evidence는 소스의 근거 문장을 짧게 요약합니다.

허용 관계 코드: uses, integrates-with, deployed-at, competes-with, related-to,
part-of, depends-on, supersedes, superseded-by

출력 형식:
```yaml
ENTITIES:
  - name: "엔티티명"
    type: person | org | product | tool | customer | concept
    description: "한 줄 설명"

RELATIONS:
  - source: "엔티티A"
    relation: 관계코드
    target: "엔티티B"
    evidence: "근거 문장 요약"
```

문서 본문:
---
{content}
---
"""


def call_llm(prompt: str, model: str) -> str:
    """LLM 호출부 — OPENAI_API_KEY 또는 ANTHROPIC_API_KEY 환경 변수 자동 감지.

    모델 prefix로 backend 결정:
      - "gpt-*", "o1-*", "o3-*" → OpenAI
      - "claude-*" → Anthropic
      - 기타 → OPENAI_API_KEY 우선, 없으면 Anthropic
    """
    use_openai = model.startswith(("gpt-", "o1-", "o3-")) or (
        not model.startswith("claude-") and os.environ.get("OPENAI_API_KEY")
    )
    if use_openai:
        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            raise RuntimeError("pip install openai") from None
        client = OpenAI()
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return resp.choices[0].message.content or ""
    # Anthropic
    try:
        import anthropic  # type: ignore
    except ImportError:
        raise RuntimeError("pip install anthropic") from None
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=model,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    # content는 list of blocks
    parts = []
    for block in resp.content:
        if hasattr(block, "text"):
            parts.append(block.text)
    return "".join(parts)


def extract_triplets(md_path: Path, model: str) -> str:
    content = md_path.read_text(encoding="utf-8")
    # YAML frontmatter 제거 (선택)
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            content = content[end + 3:].lstrip()
    prompt = PROMPT_TEMPLATE.format(content=content[:8000])  # 컨텍스트 제한
    return call_llm(prompt, model)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", type=Path, help="대상 마크다운 파일")
    ap.add_argument("--model", default="gpt-4o-mini", help="사용할 LLM 모델")
    args = ap.parse_args()

    if not args.file.exists():
        print(f"ERROR: {args.file} not found", file=sys.stderr)
        return 1

    try:
        result = extract_triplets(args.file, args.model)
    except (RuntimeError, Exception) as e:
        print(f"⚠️  {e}", file=sys.stderr)
        return 2

    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
