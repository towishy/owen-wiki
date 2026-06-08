#!/usr/bin/env python3
"""Local Korean prose metrics for WIKI/outputs Markdown.

This script is a deterministic local checker inspired by the public im-not-ai
taxonomy: it reports Korean AI-writing tells, translationese, connector habits,
and over-polish risks. It never rewrites source files and does not call an LLM.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_BASE = ROOT / "dev" / "temp" / "humanize-metrics"

FRONTMATTER_RE = re.compile(r"(?s)^---\r?\n.*?\r?\n---\r?\n(.*)$")
CODE_BLOCK_RE = re.compile(r"(?s)```.*?```|~~~.*?~~~")
HTML_COMMENT_RE = re.compile(r"(?s)<!--.*?-->")
INLINE_CODE_RE = re.compile(r"`[^`]+`")
WIKILINK_RE = re.compile(r"!?\[\[[^\]]+\]\]")
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\([^\)]+\)")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?。])\s+|\n+")
EOJEOL_RE = re.compile(r"\s+")
PUNCT_STRIP_RE = re.compile(r"[\.,!?;:()\[\]{}\"'`~、。“”‘’\-]+")
ENDING_COMMA_RE = re.compile(r"(?:고|며|지만|면서|아서|어서)\s*,")
ENDING_BOUNDARY_RE = re.compile(r"(?:고|며|지만|면서|아서|어서)(?=[\s,\.!?、。]|$)")


@dataclass(frozen=True)
class Rule:
    rule_id: str
    category: str
    severity: str
    description: str
    regex: str
    recommendation: str


@dataclass
class Finding:
    rule_id: str
    category: str
    severity: str
    description: str
    count: int
    examples: list[str]
    recommendation: str


RULES: tuple[Rule, ...] = (
    Rule("A-1", "translationese", "S1", "~에 대해/대해서", r"에\s*대해(?:서)?", "목적격 조사나 직접 서술로 줄인다."),
    Rule("A-2", "translationese", "S1", "~를 통해/통하여", r"(?:를|을)\s*통(?:해|하여)", "~로, ~해서, ~함으로써 중 문맥에 맞게 바꾼다."),
    Rule("A-3", "translationese", "S1", "~에 있어서", r"에\s*있어서", "~에서, ~을 볼 때로 바꾼다."),
    Rule("A-7", "translationese", "S1", "가지고 있다 류 직역", r"(?:가지고|갖고)\s*있", "동사나 형용사로 환원한다."),
    Rule("A-8", "translationese", "S1", "이중 피동", r"(?:되어진|되어졌|보여진|쓰여진|잊혀진|열려진|닫혀진)", "단일 피동이나 능동으로 고친다."),
    Rule("A-9", "translationese", "S2", "~에 의해 피동", r"에\s*의(?:해|하여)", "행위자를 주어로 올린다."),
    Rule("A-10", "translationese", "S2", "~할 수 있다 남발", r"[가-힣]+\s*수\s*있(?:다|습니다|음|는)", "가능성이 아니라 사실이면 단언으로 바꾼다."),
    Rule("A-16", "translationese", "S1", "영어 대명사 직역", r"(?:그녀|그것|그들|그(?:는|가|를|의|에게|와|도|만))", "생략하거나 호칭/명사구로 바꾼다."),
    Rule("A-19", "translationese", "S2", "이중 조사 결합", r"(?:에서의|에로의|으로의|에의|으로부터의|로부터의)", "절이나 구로 풀어 쓴다."),
    Rule("C-10", "structure", "S1", "콜론 부제 헤딩", r"(?m)^#{1,6}\s+[^\n:]{2,40}:\s+[^\n]+", "헤딩을 짧게 하거나 평서형으로 바꾼다."),
    Rule("C-11", "structure", "S1", "연결어미 뒤 쉼표", r"(?:고|며|지만|면서|아서|어서)\s*,", "불필요한 쉼표를 제거한다."),
    Rule("D-1", "signature", "S1", "결산 피벗", r"(?:결론적으로|따라서|이를 통해|그러므로|요약하면|정리하면)", "결론 라벨을 줄이고 문장 자체로 닫는다."),
    Rule("D-2", "signature", "S1", "공허한 시사점 표현", r"(?:시사하는 바가 크다|주목할 만하다)", "삭제하거나 구체 결론으로 바꾼다."),
    Rule("D-4", "signature", "S1", "hype 어휘", r"(?:혁신적|획기적|전례 없는|압도적|막강한|폭발적|파격적|강력한|치명적)", "수치나 구체 변화로 대체한다."),
    Rule("D-7", "signature", "S2", "X에서 Y로 변환 공식", r"[가-힣A-Za-z0-9]+에서\s+[가-힣A-Za-z0-9]+로", "한 번만 남기고 나머지는 일반 서술로 푼다."),
    Rule("E-2", "rhythm", "S2", "진행형 ~고 있다", r"고\s*있(?:다|습니다|는|었)", "단순 현재/과거로 환원 가능한지 본다."),
    Rule("F-4", "modifier", "S2", "한자어 명사화 접미", r"[가-힣]{2,}(?:성|적|화)\b", "동사/형용사나 구체 명사로 푼다."),
    Rule("G-1", "hedging", "S2", "~할 것이다 미래 단정", r"[가-힣]+\s*것(?:이다|입니다)", "현재형이나 직접 서술로 바꿀 수 있는지 본다."),
    Rule("G-2", "hedging", "S2", "~로 보인다 추정", r"(?:로|으로)\s*보인다", "근거가 충분하면 단언하고, 아니면 유지한다."),
    Rule("G-3", "hedging", "S2", "안전 균형어", r"(?:양쪽 모두|두 가지 모두|장점도 있지만|신중하게|균형)", "입장이 흐려지면 화자의 판단을 명시한다."),
    Rule("H-1", "connector", "S1", "문두 접속사 반복", r"(?m)^\s*(?:또한|따라서|즉|나아가|아울러|게다가|더욱이)\b", "문장 흐름으로 흡수하고 접속사를 줄인다."),
    Rule("I-1", "formal-noun", "S1", "~인 것이다 결말", r"(?:인|한|라는)\s*것(?:이다|입니다)", "평서형으로 닫는다."),
    Rule("I-4", "formal-noun", "S2", "권고형 결말 반복", r"(?:해야\s*한다|해야\s*합니다|할\s*필요가\s*있)", "구체 행동이나 평서 판단으로 바꾼다."),
    Rule("J-1", "visual", "S2", "본문 볼드 강조", r"\*\*[^*]{2,80}\*\*", "강조는 제목/핵심어로 제한한다."),
    Rule("J-2", "visual", "S1", "따옴표 강조", r"[\"“”‘’'][^\"“”‘’']{2,30}[\"“”‘’']", "직접 인용이 아니면 평어로 둔다."),
)


def split_frontmatter(text: str) -> tuple[str, str]:
    match = FRONTMATTER_RE.match(text)
    if match:
        return text[: match.start(1)], match.group(1)
    return "", text


def clean_for_metrics(body: str) -> str:
    text = CODE_BLOCK_RE.sub(" ", body)
    text = HTML_COMMENT_RE.sub(" ", text)
    text = INLINE_CODE_RE.sub(" ", text)
    text = WIKILINK_RE.sub(" ", text)
    return MARKDOWN_LINK_RE.sub(r"\1", text)


def split_sentences(text: str) -> list[str]:
    return [part.strip() for part in SENTENCE_SPLIT_RE.split(text.strip()) if part.strip()]


def eojeols(text: str) -> list[str]:
    return [tok for tok in EOJEOL_RE.split(text.strip()) if tok]


def strip_punct(token: str) -> str:
    return PUNCT_STRIP_RE.sub("", token)


def comma_inclusion_rate(text: str) -> float:
    sentences = split_sentences(text)
    if not sentences:
        return 0.0
    return sum(1 for sentence in sentences if "," in sentence) / len(sentences)


def comma_usage_rate(text: str) -> float:
    sentences = split_sentences(text)
    if not sentences:
        return 0.0
    return sum(sentence.count(",") for sentence in sentences) / len(sentences)


def ending_comma_rate(text: str) -> float:
    endings = ENDING_BOUNDARY_RE.findall(text)
    if not endings:
        return 0.0
    return len(ENDING_COMMA_RE.findall(text)) / len(endings)


def hanja_nominalizer_density(text: str) -> float:
    tokens = [strip_punct(token) for token in eojeols(text)]
    tokens = [token for token in tokens if token]
    if not tokens:
        return 0.0
    hits = sum(1 for token in tokens if len(token) >= 2 and token[-1] in {"성", "적", "화"})
    return hits / len(tokens)


def lexical_diversity(text: str) -> float:
    tokens = [strip_punct(token) for token in eojeols(text)]
    tokens = [token for token in tokens if token]
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)


def repeated_sentence_ending_streak(sentences: Iterable[str]) -> int:
    streak = 0
    max_streak = 0
    previous = None
    for sentence in sentences:
        token = strip_punct(sentence.split()[-1]) if sentence.split() else ""
        ending = token[-2:] if len(token) >= 2 else token
        if ending and ending == previous:
            streak += 1
        else:
            streak = 1
            previous = ending
        max_streak = max(max_streak, streak)
    return max_streak


def collect_findings(text: str) -> list[Finding]:
    findings: list[Finding] = []
    for rule in RULES:
        matches = list(re.finditer(rule.regex, text))
        if not matches:
            continue
        examples: list[str] = []
        seen: set[str] = set()
        for match in matches[:8]:
            start = max(0, match.start() - 24)
            end = min(len(text), match.end() + 24)
            example = re.sub(r"\s+", " ", text[start:end]).strip()
            if example not in seen:
                seen.add(example)
                examples.append(example)
            if len(examples) >= 3:
                break
        findings.append(Finding(rule.rule_id, rule.category, rule.severity, rule.description, len(matches), examples, rule.recommendation))
    return sorted(findings, key=lambda item: (item.severity != "S1", -item.count, item.rule_id))


def score_risk(findings: list[Finding], metrics: dict[str, float | int]) -> tuple[str, int]:
    s1 = sum(finding.count for finding in findings if finding.severity == "S1")
    s2 = sum(finding.count for finding in findings if finding.severity == "S2")
    score = (s1 * 3) + s2
    if metrics["ending_comma_rate"] >= 0.5:
        score += 3
    if metrics["comma_inclusion_rate"] >= 0.7:
        score += 1
    if metrics["hanja_nominalizer_density"] >= 0.12:
        score += 1
    if metrics["repeated_ending_max_streak"] >= 4:
        score += 2

    if score >= 16 or s1 >= 4:
        return "high", score
    if score >= 7 or s1 >= 1:
        return "medium", score
    return "low", score


def grade_result(risk_band: str, findings: list[Finding]) -> str:
    s1 = sum(finding.count for finding in findings if finding.severity == "S1")
    s2 = sum(finding.count for finding in findings if finding.severity == "S2")
    if risk_band == "high":
        return "D"
    if risk_band == "low" and s1 == 0 and s2 <= 2:
        return "A"
    if risk_band in {"low", "medium"} and s1 <= 1 and s2 <= 6:
        return "B"
    if risk_band == "medium" or s1 <= 3:
        return "C"
    return "D"


def analyze_file(path: Path, genre: str) -> dict:
    raw = path.read_text(encoding="utf-8")
    _frontmatter, body = split_frontmatter(raw)
    metric_text = clean_for_metrics(body)
    sentences = split_sentences(metric_text)
    tokens = [strip_punct(token) for token in eojeols(metric_text)]
    tokens = [token for token in tokens if token]
    findings = collect_findings(metric_text)
    metrics: dict[str, float | int] = {
        "char_count": len(metric_text),
        "sentence_count": len(sentences),
        "token_count": len(tokens),
        "comma_inclusion_rate": round(comma_inclusion_rate(metric_text), 4),
        "comma_usage_rate": round(comma_usage_rate(metric_text), 4),
        "ending_comma_rate": round(ending_comma_rate(metric_text), 4),
        "hanja_nominalizer_density": round(hanja_nominalizer_density(metric_text), 4),
        "lexical_diversity": round(lexical_diversity(metric_text), 4),
        "repeated_ending_max_streak": repeated_sentence_ending_streak(sentences),
    }
    risk_band, risk_score = score_risk(findings, metrics)
    return {
        "schema": "wiki-humanize-metrics.v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_path": str(path),
        "genre": genre,
        "risk_band": risk_band,
        "risk_score": risk_score,
        "grade": grade_result(risk_band, findings),
        "metrics": metrics,
        "finding_counts": {
            "S1": sum(finding.count for finding in findings if finding.severity == "S1"),
            "S2": sum(finding.count for finding in findings if finding.severity == "S2"),
            "total": sum(finding.count for finding in findings),
        },
        "findings": [asdict(finding) for finding in findings],
        "do_not": ["numbers", "dates", "proper nouns", "product names", "direct quotes", "legal clauses", "code blocks"],
    }


def safe_stem(path: Path) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "-", path.stem)[:80] or "document"


def render_report(result: dict) -> str:
    lines = [
        f"# Humanize Metrics - {Path(result['source_path']).name}",
        "",
        f"- risk_band: `{result['risk_band']}`",
        f"- risk_score: `{result['risk_score']}`",
        f"- grade: `{result['grade']}`",
        f"- findings: `S1={result['finding_counts']['S1']}` / `S2={result['finding_counts']['S2']}` / `total={result['finding_counts']['total']}`",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for key, value in result["metrics"].items():
        lines.append(f"| `{key}` | {value} |")

    lines.extend(["", "## Top Findings", ""])
    if not result["findings"]:
        lines.append("- No configured S1/S2 Korean AI-style signal was found.")
    else:
        for finding in result["findings"][:12]:
            examples = "; ".join(f"`{example}`" for example in finding["examples"][:2]) or "n/a"
            lines.append(
                f"- `{finding['rule_id']}` {finding['severity']} {finding['description']} "
                f"x{finding['count']} - {finding['recommendation']}\n  - examples: {examples}"
            )

    lines.extend([
        "",
        "## Local Editing Guardrails",
        "",
        "- Treat this as deterministic lint, not an automatic rewrite.",
        "- Preserve numbers, dates, product names, direct quotes, legal clauses, and code.",
        "- Prioritize S1 findings first and keep edits local to detected spans.",
        "- Warn above 30% rewrite rate; stop and review above 50%.",
    ])
    return "\n".join(lines) + "\n"


def resolve_paths(values: list[str]) -> list[Path]:
    paths: list[Path] = []
    for value in values:
        path = Path(value)
        if path.is_dir():
            paths.extend(sorted(path.rglob("*.md")))
            paths.extend(sorted(path.rglob("*.mdx")))
        else:
            paths.append(path)
    return paths


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="+", help="Markdown files or directories to inspect")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory")
    parser.add_argument("--genre", default="auto", help="Genre hint stored in the report")
    parser.add_argument("--fail-on", choices=["off", "medium", "high"], default="off", help="Exit non-zero when risk meets this band")
    parser.add_argument("--quiet", action="store_true", help="Only print output directory and exit summary")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out_dir = args.out_dir or (DEFAULT_OUT_BASE / datetime.now().strftime("%Y%m%d-%H%M%S"))
    out_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    for path in resolve_paths(args.paths):
        if path.suffix.lower() not in {".md", ".mdx"}:
            continue
        result = analyze_file(path, genre=args.genre)
        results.append(result)
        stem = safe_stem(path)
        (out_dir / f"{stem}.humanize.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (out_dir / f"{stem}.humanize.md").write_text(render_report(result), encoding="utf-8")

    index_payload = {
        "schema": "wiki-humanize-metrics-index.v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "count": len(results),
        "results": [
            {
                "source_path": result["source_path"],
                "risk_band": result["risk_band"],
                "risk_score": result["risk_score"],
                "grade": result["grade"],
                "finding_counts": result["finding_counts"],
            }
            for result in results
        ],
    }
    (out_dir / "index.json").write_text(json.dumps(index_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = ["# Humanize Metrics Index", "", "| File | Risk | Score | Grade | S1 | S2 |", "|---|---|---:|---:|---:|---:|"]
    for result in results:
        counts = result["finding_counts"]
        lines.append(
            f"| `{Path(result['source_path']).name}` | `{result['risk_band']}` | {result['risk_score']} | {result['grade']} | {counts['S1']} | {counts['S2']} |"
        )
    (out_dir / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    high = sum(1 for result in results if result["risk_band"] == "high")
    medium = sum(1 for result in results if result["risk_band"] == "medium")
    if not args.quiet:
        print(f"Humanize metrics output: {out_dir}")
        for result in results:
            print(f"{result['risk_band']:>6} score={result['risk_score']:>2} grade={result['grade']} {result['source_path']}")
    else:
        print(out_dir)

    if args.fail_on == "high" and high:
        return 4
    if args.fail_on == "medium" and (high or medium):
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
