# Owen-WIKI Template Kit

> **LLM Wiki + Knowledge Graph 온톨로지** 기반의 자기 성장형 지식 관리 시스템 템플릿.
> 이 킷을 사용하면 Owen의 WIKI 저장소와 동일한 구조의 개인 위키를 구축할 수 있다.

**Version**: 1.11.0 (2026-04-25)

**Origin**: Owen's LLM Wiki — Microsoft Security 도메인 339+ 페이지 / raw 5,798 파일 / **변환율 100%** 운영 경험 기반

**Based on**: Andrej Karpathy의 LLM Wiki 패턴 + Nodus Labs Knowledge Graph 확장 + LightRAG (HKUDS, EMNLP2025) 트리플렛/리랭킹 차용

---


## 6가지 핵심 특징

1. **🤖 LLM-Native KB** — AGENTS.md 하나로 인제스트·질의·점검·온톨로지·산출물까지 자율 운영. 사람은 raw 입력과 outputs 검토만.
2. **📂 3-Layer 분리** — `raw/`(불변 입력) → `wiki/`(LLM 정제) → `outputs/`(공동 산출). 책임 경계가 깔끔.
3. **🕸️ 온톨로지 + 갭 분석** — 위키링크와 별개로 `[[A]] [관계] [[B]]` 트리플렛을 `wiki/ontology/`에 누적. 클러스터·허브·갭을 데이터로 파악.
4. **🧲 자동 클러스터 허브 (v1.7)** — 4,000+ 파일 규모 raw/도 개별 ingest 없이 허브 페이지로 일괄 흡수. **변환율 100% 달성**.
5. **📋 Action Queue (v1.9)** — registry 승격, synthesis 후보, 태그 정규화, raw 지식화 등급을 자동 산출.
6. **🧭 Ops Dashboard (v1.10)** — quality gate, action queue, promotion lifecycle, ontology sidecar 핵심 지표를 단일 진입점으로 통합.
7. **🎚️ Operations Precision (v1.11)** — registry 후보 scoring/dedupe, lifecycle CLI, relation quality, tag drift 0 목표 상태를 운영 자동화에 포함.
8. **📊 운영 검증된 스케일** — 661 페이지 / 6,000+ 위키링크 / **Microsoft Security 27/27 제품 100% 커버** / 깨진 링크 0 / 고아 0 — 모두 실측.
9. **📦 재사용 가능한 템플릿 킷** — 외부 git 저장소(`/Users/owen/work/owen-wiki`)로 분리 배포, 누구나 같은 구조의 LLM Wiki 구축 가능.

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
| **대량 흡수** | 4,000+ 파일도 ingest 없이 처리 (v1.7) | [auto-cluster-hubs.py](scripts/auto-cluster-hubs.py) + [absorb-remaining-uningested.py](scripts/absorb-remaining-uningested.py) |
| **다음 액션 자동화** | registry 승격·synthesis 후보·태그 정규화 후보 산출 (v1.9) | [wiki-action-queue.py](scripts/wiki-action-queue.py) |
| **후보 품질 정밀화** | generic registry 감점·part 후보 dedupe·broad product mix 감점 (v1.11) | [wiki-action-queue.py](scripts/wiki-action-queue.py) |
| **운영 대시보드** | 품질·큐·승격 상태·온톨로지 지표 단일 진입점 (v1.10) | [wiki-ops-dashboard.py](scripts/wiki-ops-dashboard.py) |
| **승격 라이프사이클** | source registry 후보를 candidate→promoted 흐름으로 추적 (v1.10) | [registry-promotion-lifecycle.py](scripts/registry-promotion-lifecycle.py) |
| **온톨로지 기계판독** | 관계 weight/evidence/path를 JSONL로 제공 (v1.9) | [build-ontology-sidecar.py](scripts/build-ontology-sidecar.py) |
| **관계 품질 개선** | 약한 `related-to` 관계 치환 후보 산출 (v1.11) | [check-ontology-relations.py](scripts/check-ontology-relations.py) |
| **무결성** | 7종 lint 자동화 | tags / ontology / orphans / broken-links / confidence-decay / uningested / hub-sources |
| **품질 게이트** | PR에서 구조 품질 기준 강제 (v1.9) | [wiki-quality-gates.py](scripts/wiki-quality-gates.py) |
| **도메인 깊이** | MS Security 100% | 5축 태그 체계 596종 |
| **산출물 다양성** | KB 외 PPTX/DOCX/HTML/Mermaid | 4종 카테고리 |
| **외부 자료 흡수** | PPTX/PDF/DOCX/XLSX → MD | markitdown 1차 + 폴백 다중 엔진 |
| **감사·롤백** | 모든 작업 추적 | git + log.md append-only + raw 불변 원칙 |
| **시각화** | 위키 그래프 자동 생성 | [wiki-graph-viz.py](scripts/wiki-graph-viz.py) (Louvain 커뮤니티 + 인터랙티브 HTML) |


## 이 킷에 포함된 파일

### 핵심 문서·템플릿

| 파일 | 용도 | 행동 |
|------|------|------|
| `README.md` | 이 파일 — 전체 가이드 | 읽기 |
| `AGENTS.md` | LLM 에이전트 스키마 v1.11 (복사하여 사용) | 프로젝트 루트에 복사 |
| `SETUP-GUIDE.md` | 단계별 설정 가이드 | 따라하기 |
| `CHANGELOG.md` | 템플릿 킷 버전 변경 이력 | 참고 |
| `templates/` | 위키 페이지 템플릿 5종 | `templates/`에 복사 |
| `starter-files/` | index.md, log.md, overview.md 초기본 | 프로젝트 루트에 복사 |
| `ontology-templates/` | 온톨로지 파일 초기본 | `wiki/ontology/`에 복사 |

### 스크립트 22종+ (`scripts/`)

**기본 lint·통계 (8종)**

| 스크립트 | 용도 |
|---------|------|
| `wiki-stats.py` | 페이지·태그·confidence 분포 통계 |
| `find-orphans.py` | 인바운드 0 페이지 탐지 |
| `check-tags.py` | 태그 프리픽스 컴플라이언스 검사 |
| `scan-broken-links.py` | 깨진 위키링크 스캔 |
| `check-ontology.py` | 온톨로지 위키링크 무결성 검사 |
| `check-confidence-decay.py` | 90일 aging / 180일 stale 자동 분류 |
| `sanitize-ingest.py` | PII 9패턴 사전 점검 (Ingest 0단계) |
| `extract-raw-sources.py` | PPTX/PDF/DOCX/XLSX → markdown (markitdown 우선) |

**v1.7.0 신규 — 자동 클러스터 허브 & 정합성 (10종)**

| 스크립트 | 용도 |
|---------|------|
| `find-uningested-raw.py` | raw/ 미참조 파일 스캔 (NFC normalize + 특수문자 매칭) |
| `auto-cluster-hubs.py` | 미수집 raw 후보 스캔 → 2단계 경로 그룹핑 → 허브 summary 자동 생성 |
| `absorb-remaining-uningested.py` | 잔여 미수집 파일을 라우팅 룰로 기존 허브에 흡수 |
| `apply-default-confidence.py` | 정책 기반 confidence/last_confirmed 일괄 부여 |
| `rebalance-confidence.py` | 1차 소스(type/mslearn 등) confidence 0.85+ 재평가 |
| `auto-extract-triplets.py` | LLM 기반 ENTITIES/RELATIONS 트리플렛 추출 스켈레톤 |
| `append-ontology.py` | 트리플렛 YAML을 *-ontology.md에 dedupe 후 APPEND |
| `fix-broken-wikilinks.py` | ALIASES dict 기반 깨진 위키링크 자동 교정 |
| `fix-hub-sources.py` | 손상된 클러스터 허브 sources YAML 복구 (mojibake/backslash → UTF-8) |
| `gen-hub-category-index.py` | 허브 sources를 서브폴더로 그룹화한 본문 인덱스 생성 |

**시각화 (1종)**

| 스크립트 | 용도 |
|---------|------|
| `wiki-graph-viz.py` | 위키링크 그래프 → Louvain 커뮤니티 → pyvis 인터랙티브 HTML + GRAPH_REPORT.md |

**v1.9.0 신규 — Action Queue & Quality Gates**

| 스크립트 | 용도 |
|---------|------|
| `absorb-uningested-subhubs.py` | remaining raw 후보를 source registry sub-hub로 분할 수집 |
| `wiki-action-queue.py` | registry 승격 후보, synthesis 후보, 태그 정규화 후보, raw 지식화 등급, graph/search 랭킹 힌트 생성 |
| `build-ontology-sidecar.py` | Markdown ontology를 relation weight/evidence/path 포함 JSONL로 변환 |
| `wiki-quality-gates.py` | broken/orphan/tag/stub/remaining raw parent hub 링크를 CI gate로 강제 |
| `apply-tag-aliases.py` | `tag-aliases.yml` 기반 태그 alias 실제 적용 |
| `weekly-gap-report.py` | Action Queue를 주간 갭 리포트에 포함 |

**v1.10.0 신규 — Ops Dashboard & Promotion Lifecycle**

| 스크립트 | 용도 |
|---------|------|
| `registry-promotion-lifecycle.py` | source registry 승격 후보를 candidate/sampled/promoted/deferred/rejected 상태로 추적 |
| `wiki-ops-dashboard.py` | quality gate, action queue, promotion lifecycle, ontology sidecar 핵심 지표를 단일 운영 대시보드로 생성 |

**v1.11.0 신규 — Operations Precision**

| 스크립트 | 용도 |
|---------|------|
| `wiki-action-queue.py` | generic registry 감점, broad product mix 감점, `part-*` 후보 group dedupe |
| `registry-promotion-lifecycle.py` | `--set PAGE status --note ... --target-summary ...` CLI 상태 변경 지원 |
| `wiki-ops-dashboard.py` | 이전 실행 대비 delta와 ontology relation quality 요약 표시 |
| `check-ontology-relations.py` | 약한 `related-to` 관계를 더 구체적인 relation으로 바꿀 후보 리포트 생성 |

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
cp <path-to>/owen-wiki/AGENTS.md ./AGENTS.md
cp <path-to>/owen-wiki/starter-files/* ./
cp <path-to>/owen-wiki/templates/* ./templates/
cp <path-to>/owen-wiki/ontology-templates/* ./wiki/ontology/
cp <path-to>/owen-wiki/scripts/* ./scripts/   # v1.11.0: Operations Precision 포함

# 4. AGENTS.md를 열어 도메인/경로를 자신의 것으로 수정

# 5. Git 초기화 (선택)
git init && echo ".venv/\nraw/extracted/\ngraphify-out/" > .gitignore

# 6. 첫 소스를 raw/에 넣고 LLM에게 "ingest 해줘" 지시
#    → sanitize-ingest.py가 자동으로 PII 점검 후 진행
#    → 대량 자료는 auto-cluster-hubs.py로 일괄 흡수 (v1.7)
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
| **Cluster Hub Absorb (v1.7)** | 대량 raw/ 추가 | `find-uningested-raw.py` → `auto-cluster-hubs.py` → `absorb-remaining-uningested.py` → `gen-hub-category-index.py` |

> **v1.3.0 신규 프로토콜** — Ingest 시 `(주체, 관계, 객체)` 트리플렛을 ENTITIES/RELATIONS YAML 형식으로 먼저 추출 → 온톨로지 자동 APPEND. Query 시 후보 페이지 6개 이상이면 메타데이터 기반 7개 기준 점수화로 토큰 절감.

> **v1.4.0 신규 라이프사이클** — YAML 프론트매터에 `confidence` (0~1), `last_confirmed`, `stale_after`, `supersedes`, `superseded_by` 5개 필드 추가. Ingest 0단계에 PII 사전 점검 도입. Lint 시 90일 aging / 180일 stale 자동 분류.

> **v1.5.0 그래프 시각화** — `scripts/wiki-graph-viz.py`로 위키링크 → NetworkX 그래프 → Louvain 커뮤니티 탐지 → 인터랙티브 HTML + GRAPH_REPORT.md 자동 생성. 500+ 페이지 스케일 전환 전 구조 분석 기반.

> **v1.6.0 다이어그램 표준** — Mermaid 우선 + 4색 팔레트 (General/Highlight/Decision/Success). ASCII 박스 금지, A3 PDF 인쇄 친화 규칙.

> **v1.7.0 자동 클러스터 허브** — 4,000+ 파일 raw/도 개별 ingest 없이 허브 페이지로 흡수. **변환율 100% 달성** (Owen WIKI 운영 검증: 5,798/5,798). 임계값 3+ 파일, confidence 자동 허브 0.55, scanner NFC normalize + 특수문자(괄호·작은따옴표) 매칭 지원.

---

## 버전 호환

이 킷은 Owen의 WIKI가 발전할 때마다 함께 버전업됩니다.
변경 이력은 `CHANGELOG.md`를 확인하세요.

---

## 라이선스

MIT — 자유롭게 사용, 수정, 배포 가능.
