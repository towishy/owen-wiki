# Owen-WIKI Template Kit

> **LLM Wiki + Knowledge Graph 온톨로지** 기반의 자기 성장형 지식 관리 시스템 템플릿.
> 이 킷을 사용하면 Owen의 WIKI 저장소와 동일한 구조의 개인 위키를 구축할 수 있다.

**Version**: 1.4.0 (2026-04-18)

**Origin**: Owen's LLM Wiki — Microsoft Security 도메인 216+ 페이지 운영 경험 기반

**Based on**: Andrej Karpathy의 LLM Wiki 패턴 + Nodus Labs Knowledge Graph 확장 + LightRAG (HKUDS, EMNLP2025) 트리플렛/리랭킹 차용

---


## 5가지 핵심 특징

1. **🤖 LLM-Native KB** — AGENTS.md 하나로 인제스트·질의·점검·온톨로지·산출물까지 자율 운영. 사람은 raw 입력과 outputs 검토만.
2. **📂 3-Layer 분리** — `raw/`(불변 입력) → `wiki/`(LLM 정제) → `outputs/`(공동 산출). 책임 경계가 깔끔.
3. **🕸️ 온톨로지 + 갭 분석** — 위키링크와 별개로 `[[A]] [관계] [[B]]` 트리플렛을 `wiki/ontology/`에 누적. 클러스터·허브·갭을 데이터로 파악.
4. **📊 운영 검증된 스케일** — 294 페이지 / 3,853 위키링크 / **Microsoft Security 27/27 제품 100% 커버** / git 63커밋 / log 71항목 — 모두 실측.
5. **📦 재사용 가능한 템플릿 킷** — [Owen-WIKI/](outputs/Owen-WIKI/)로 누구나 같은 구조의 LLM Wiki 구축 가능 (외부 git 저장소와 이중 동기화).

---

## 장점 한눈에 보기

| 영역 | 장점 | 메커니즘 |
|------|------|---------|
| **신뢰도** | 페이지마다 출처 풍부도 추적 | `confidence` 0.0~1.0 (5단계 가이드) |
| **라이프사이클** | 옛 정보 자동 분류 | `last_confirmed`/`stale_after` + 90/180일 aging/stale |
| **버전 관리** | 옛 페이지 명시적 대체 | `supersedes`/`superseded_by` + 산출물 자동 신버전 권장 |
| **개인정보 보호** | 인제스트 0단계 PII 차단 | [sanitize-ingest.py](scripts/sanitize-ingest.py) 9패턴 |
| **검색 효율** | 토큰 절감 답변 | 5-Route 전략 + 9기준 Relevance Scoring |
| **인제스트 정밀도** | 트리플렛 구조 추출 | LightRAG 차용 ENTITIES/RELATIONS YAML |
| **인덱싱 비용** | 파일 추가 시 ~50 토큰 | 2-tier + Smart Diff 3-tier 전략 |
| **무결성** | 5종 lint 자동화 | tags / ontology / orphans / broken-links / confidence-decay |
| **도메인 깊이** | MS Security 100% | 5축 태그 체계 556종 |
| **산출물 다양성** | KB 외 PPTX/DOCX/HTML/Mermaid | [outputs/](outputs/) 4종 카테고리 |
| **외부 자료 흡수** | PPTX/PDF/DOCX/XLSX → MD | markitdown 1차 + 폴백 다중 엔진 |
| **감사·롤백** | 모든 작업 추적 | git + log.md append-only + raw 불변 원칙 |


## 이 킷에 포함된 파일

| 파일 | 용도 | 행동 |
|------|------|------|
| `README.md` | 이 파일 — 전체 가이드 | 읽기 |
| `AGENTS.md` | LLM 에이전트 스키마 (복사하여 사용) | 프로젝트 루트에 복사 |
| `SETUP-GUIDE.md` | 단계별 설정 가이드 | 따라하기 |
| `templates/` | 위키 페이지 템플릿 5종 | `templates/`에 복사 |
| `starter-files/` | index.md, log.md, overview.md 초기본 | 프로젝트 루트에 복사 |
| `ontology-templates/` | 온톨로지 파일 초기본 | `wiki/ontology/`에 복사 |
| `scripts/extract-raw-sources.py` | 바이너리→마크다운 추출 스크립트 | `scripts/`에 복사 |
| `scripts/wiki-stats.py` | 위키 저장소 통계 | `scripts/`에 복사 |
| `scripts/find-orphans.py` | 고아 페이지 탐지 | `scripts/`에 복사 |
| `scripts/check-tags.py` | 태그 프리픽스 준수 검사 | `scripts/`에 복사 |
| `scripts/scan-broken-links.py` | 깨진 위키링크 스캔 | `scripts/`에 복사 |
| `scripts/check-ontology.py` | 온톨로지 정합성 검사 | `scripts/`에 복사 |
| `CHANGELOG.md` | 템플릿 킷 버전 변경 이력 | 참고 |

---

## Quick Start (5분 세팅)

```bash
# 1. 프로젝트 폴더 생성
mkdir my-wiki && cd my-wiki

# 2. 디렉토리 구조 생성
mkdir -p raw/{assets,articles,papers,notes,extracted} \
         wiki/{entities,concepts,summaries,comparisons,synthesis,ontology} \
         outputs/{presentations,reports,workshops,drafts} \
         scripts templates

# 3. Owen-WIKI 킷에서 파일 복사
cp <path-to>/Owen-WIKI/AGENTS.md ./AGENTS.md
cp <path-to>/Owen-WIKI/starter-files/* ./
cp <path-to>/Owen-WIKI/templates/* ./templates/
cp <path-to>/Owen-WIKI/ontology-templates/* ./wiki/ontology/
cp <path-to>/Owen-WIKI/scripts/* ./scripts/   # v1.4.0에서 스크립트 8종 포함

# 4. AGENTS.md를 열어 도메인/경로를 자신의 것으로 수정

# 5. Git 초기화 (선택)
git init && echo ".venv/\nraw/extracted/" > .gitignore

# 6. 첫 소스를 raw/에 넣고 LLM에게 "ingest 해줘" 지시
#    → sanitize-ingest.py가 자동으로 PII 점검 후 진행
```

상세 가이드: `SETUP-GUIDE.md`

---

## 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────┐
│                    Knowledge Pipeline                        │
│                                                              │
│  raw/ (입력) → wiki/ (정제 + 온톨로지) → outputs/ (산출)   │
│                                     ↑                  ↑    │
│                                관계 추출          갭 기반 생성│
└─────────────────────────────────────────────────────────────┘
```

### 4개 레이어

| 레이어 | 소유자 | 역할 |
|--------|--------|------|
| `raw/` | 사용자 | 원본 소스 (불변) |
| `wiki/` | LLM | 정제된 지식 페이지 + 온톨로지 |
| `wiki/ontology/` | LLM | 관계 그래프 + 갭 분석 (wiki/ 하위) |
| `outputs/` | 공동 | 최종 산출물 |

### 5개 페이지 타입

| 타입 | 폴더 | 용도 | 예시 |
|------|------|------|------|
| Entity | `wiki/entities/` | 인물, 조직, 도구, 제품 | `openai.md`, `python.md` |
| Concept | `wiki/concepts/` | 이론, 프레임워크, 방법론 | `machine-learning.md` |
| Summary | `wiki/summaries/` | 소스별 요약 | `attention-is-all-you-need.md` |
| Comparison | `wiki/comparisons/` | 비교 분석 | `pytorch-vs-tensorflow.md` |
| Synthesis | `wiki/synthesis/` | 종합 분석, 허브 | `overview.md` |

### 4개 워크플로우

| 워크플로우 | 트리거 | 핵심 동작 |
|------------|--------|-----------|
| **Ingest** (10단계) | 새 소스 추가 | **PII 점검(v1.4)** → 트리플릿 추출 (LightRAG) → 요약 생성 → 엔티티/개념 업데이트 → 온톨로지 APPEND |
| **Query** | 질문 | 5-Route 탐색 → Relevance Scoring 9기준 (신뢰도+노후 포함) → 합성 답변 |
| **Lint** (11단계) | 주기적 | 모순/고아/갭 검사 + **노후 점검(v1.4)** → gap-analysis.md 갱신 |
| **Ontology Update** | 대규모 변경 후 | 클러스터-갭 재분석 → overview.md 갱신 |

> **v1.3.0 신규 프로토콜** — Ingest 시 `(주체, 관계, 객체)` 트리플렛을 ENTITIES/RELATIONS YAML 형식으로 먼저 추출 → 온톨로지 자동 APPEND. Query 시 후보 페이지 6개 이상이면 메타데이터 기반 7개 기준(제목/태그/타입/최신성/소스/중심성/백링크) 점수화로 토큰 절감.

> **v1.4.0 신규 라이프사이클** — YAML 프론트매터에 `confidence` (0~1), `last_confirmed`, `stale_after`, `supersedes`, `superseded_by` 5개 필드 추가. Ingest 0단계에 PII 사전 점검(`scripts/sanitize-ingest.py`) 도입. Lint 시 `scripts/check-confidence-decay.py`로 90일 aging / 180일 stale 자동 분류. Relevance Scoring에 신뢰도 가중과 노후 페널티 반영.

---

## 버전 호환

이 킷은 Owen의 WIKI가 발전할 때마다 함께 버전업됩니다.
변경 이력은 `CHANGELOG.md`를 확인하세요.

---

## 라이선스

MIT — 자유롭게 사용, 수정, 배포 가능.
