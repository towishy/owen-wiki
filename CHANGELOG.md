# Owen-WIKI Template Kit — Changelog

이 파일은 Owen-WIKI 템플릿 킷의 버전 변경 이력을 기록한다.
Owen의 WIKI 저장소가 발전할 때마다 이 킷도 함께 버전업된다.

---

## [1.7.0] — 2026-04-24

### 자동 클러스터 허브 정책 + 100% raw→wiki 변환 + 스크립트 10종 추가

대규모 raw/ 자료(고객사별 동일 워크숍 사본 등)를 개별 ingest 하지 않고 **클러스터 허브 페이지로 일괄 sources 등록**하는 운영 정책을 정식 채택. 운영 결과 **raw → wiki 변환율 100% (5,798/5,798)**, **깨진 링크 0**, **고아 페이지 0** 달성.

**AGENTS.md 변경:**
- `### 자동 클러스터 허브 정책 (v1.7+)` 신규 섹션 (스케일 & 도구 하위)
  - 임계값: 3개 이상 파일이 동일 클러스터 키 공유 시 허브 자동 생성
  - confidence 기본값: 자동 허브 0.55 / 큐레이션 허브 0.65 / 1차 소스 summary 0.85+
  - SKIP_PREFIX/SKIP_CONTAINS 패턴, NFC normalize + 특수문자 매칭 규칙
- `### 현재 규모` 갱신 (페이지 339, 위키링크 4,428, 변환율 100%, 그래프 통계 추가)
- `## 스케일 & 도구` 단순화 — 그래프 시각화 상세 섹션은 v1.5.0과 중복이라 본문에서 제거 (스크립트는 유지)

**스크립트 추가 (10종):**

| 파일 | 용도 |
|------|------|
| `auto-cluster-hubs.py` | 미수집 raw 후보 스캔 → 2단계 경로 그룹핑 → 허브 summary 자동 생성 |
| `absorb-remaining-uningested.py` | 잔여 미수집 파일을 라우팅 룰로 기존 허브에 흡수 |
| `find-uningested-raw.py` | raw/ 미참조 파일 스캔 (NFC normalize + 괄호·대괄호·작은따옴표 지원) |
| `fix-broken-wikilinks.py` | ALIASES dict 기반 깨진 위키링크 자동 교정 + 이미지 마크다운 변환 |
| `apply-default-confidence.py` | 정책 기반 confidence/last_confirmed 일괄 부여 |
| `auto-extract-triplets.py` | LLM 기반 ENTITIES/RELATIONS 트리플렛 추출 스켈레톤 (LightRAG 형식) |
| `fix-hub-sources.py` | 손상된 클러스터 허브 sources YAML 복구 (mojibake/backslash → UTF-8) |
| `append-ontology.py` | 트리플렛 YAML을 *-ontology.md에 dedupe 후 APPEND |
| `rebalance-confidence.py` | type/mslearn·type/ninja 등 1차 소스 페이지 confidence 재평가 |
| `gen-hub-category-index.py` | 허브 sources를 1단계 경로(서브폴더)로 그룹화한 본문 인덱스 생성 |

**도입 이유:**

- 4,000+ 파일 규모 raw/(고객사 워크숍·MS 보안 교육 자료 등)를 1:1 summary로 처리 시 토큰·시간 폭증
- 허브 + sources 등록만으로도 LLM 검색·요약·산출 가능 → "흡수" 경제성 확보
- 운영 검증: 변환율 60% → 100% 달성, 동시에 깨진 링크 11→0

---

## [1.6.0] — 2026-04-23

### 다이어그램 표준 섹션 신설 (Mermaid 우선 + 4색 팔레트)

- AGENTS.md에 **«다이어그램 표준 (Mermaid 우선)»** 섹션 추가
- ASCII 박스 다이어그램 금지 명시, Mermaid 우선 원칙
- A3 PDF 가로폭 제한 규칙 정리 (노드 6개 이하, TB 세로 방향, Gantt 7~14일 단위)
- edge label에 `<br/>` 금지 → `"..."` 따옴표 규칙 명시
- **표준 4색 팔레트** 추가: General / Highlight / Decision / Success (일반 흐름도)
- **제품별 식별 색상** 정리: Entra/MDE/MDI/Intune/Purview/GSA/CA (제품 구분 필요 시만 사용)

### 이유

다수 산출물에서 일관된 시각 언어 필요, A3 PDF 출력 시 잘림·명도 문제 반복 발생 → 표준화로 재작업 최소화.

---

## [1.5.0] — 2026-04-23

### 위키 그래프 시각화 스크립트 + graphify-out 레이어

위키 전체 [[위키링크]] 그래프를 자동 시각화하는 스크립트 도입. Louvain 커뮤니티 탐지, God Node/Betweenness Centrality 분석, 인터랙티브 HTML 시각화를 제공.

**변경사항:**
- `scripts/wiki-graph-viz.py` (신규): wiki/ 폴더의 모든 .md에서 [[위키링크]] 파싱 → NetworkX 방향 그래프 구축 → Louvain 커뮤니티 탐지 → pyvis 인터랙티브 HTML + GRAPH_REPORT.md + graph.json 생성
- `AGENTS.md` · 볼트 구조: `graphify-out/` 폴더 추가 (graph.html, GRAPH_REPORT.md, graph.json)
- `AGENTS.md` · 스케일 & 도구: **그래프 시각화** 섹션 신설 — 의존성, 사용법, 출력 파일, 분석 항목 표, 실행 주기 안내
- 의존성: `networkx`, `pyvis`, `python-louvain` (pip install)

**분석 항목:**
- God Nodes (Degree Top 20): 위키 핵심 허브 페이지 파악
- Betweenness Centrality (Top 10): 구조적 병목 노드 식별
- Louvain 커뮤니티: 자동 의미 클러스터링 (카테고리와 비교 가능)
- 고아 노드 / 인바운드 0 페이지: Lint 시 보강 대상
- 커뮤니티 간 엣지: 예상 외 관계 발견 (Surprise Edge)

**도입 이유:**
- Obsidian Graph View는 시각적이지만 정량 분석(중심성, 커뮤니티) 불가
- 온톨로지 파일(.md) 기반 수동 관계 관리의 한계 → 위키링크에서 자동 그래프 생성
- 500+ 페이지 스케일 전환 전 구조 분석 기반 마련
- Graphify(graphify.net) 개념을 도메인 지식 위키에 맞게 경량 구현

---

## [1.4.0] — 2026-04-21

### Confidence/Provenance 필드 + Supersession + PII 사전 점검

rohitg00/llm-wiki v2 분석을 바탕으로 운영 안정성을 강화하는 3가지 라이프사이클 메커니즘 도입.

**변경사항:**
- `templates/*.md` 5종: YAML 프론트매터에 `confidence`, `last_confirmed`, `stale_after`, `supersedes`, `superseded_by` 5개 필드 추가 (선택, 신규 페이지부터 권장)
- `AGENTS.md` · 페이지 컨벤션: **Confidence Scoring 가이드** 표(0.0~1.0 5단계), **Last Confirmed / Stale After 규칙** (90일 aging / 180일 stale), **Supersession 규칙** 신설
- `AGENTS.md` · Ingest 워크플로우:
  - 0단계 **PII 사전 점검** 추가 (sanitize-ingest.py)
  - 7단계 **supersedes/superseded_by 프론트매터 기록** 추가 (총 9 → 10단계)
- `AGENTS.md` · Query Relevance Scoring:
  - 신뢰도(+2 / +1) 항목 추가
  - 노후 페널티(aging −1 / stale −3) 추가
  - superseded_by 보유 페이지 자동 후순위
- `AGENTS.md` · Lint 워크플로우: 노후 점검(7) + PII 점검(8) 단계 추가 (총 9 → 11단계)
- `AGENTS.md` · 트리플렛 추출 프로토콜: 관계 코드에 `supersedes`, `superseded-by` 추가
- `scripts/check-confidence-decay.py` (신규): last_confirmed/updated 기반 aging/stale 자동 분류, `--apply`로 태그 자동 부여
- `scripts/sanitize-ingest.py` (신규): EMAIL/IPv4/IPv6/GUID/JWT/Bearer/AWS Key/한국 RRN/전화번호/Azure SAS 9개 패턴 탐지, MS 공식 도메인 화이트리스트, `--mask`로 마스킹 사본 생성
- `scripts/wiki-stats.py`: confidence 분포 5버킷 + superseded/aging/stale 카운트 추가
- `README.md`: 버전 1.4.0

**도입 이유:**
- **Confidence**: 모든 페이지가 동등한 권위로 취급되던 한계 해소. Microsoft 공식 vs 추정 정보 구분.
- **Supersession**: 자주 갱신되는 MS 제품 정보의 옛 버전을 명시적으로 추적, 산출물에서 자동 신버전 권장.
- **PII 필터**: 컨설팅 도메인(`raw/security-onsite-reports/` 4,392 파일) 인제스트 시 고객 정보 사전 차단.
- **노후곡선**: 1년 전 정보와 어제 정보의 동등 가중 문제 해소.

**rohitg00 v2와의 차이:**
- v2는 자동 망각·decay score 계산까지 제안 → Owen은 단순 임계 분류(90/180일)로 시작
- Working/Episodic/Semantic/Procedural 메모리 4계층은 미도입 (현재 raw/wiki/outputs 3계층 유지)
- Auto-crystallization, Self-healing lint 모순 탐지는 다음 버전(v1.5+)으로 보류

---

## [1.3.0] — 2026-04-18

### LightRAG 차용 워크플로우 도입 (트리플렛 추출 + Relevance Scoring)

LightRAG (HKUDS, EMNLP2025) 분석을 바탕으로 Ingest와 Query 워크플로우에 구조화된 프로토콜 두 개를 추가.

**변경사항:**
- `AGENTS.md` · Ingest 워크플로우:
  - 새 단계 2 **트리플렛 추출** 추가 (기존 8단계 → 9단계)
  - 새 하위 섹션 **트리플렛 추출 프로토콜 (LightRAG 차용)** — ENTITIES/RELATIONS YAML 형식, evidence 필드, 명시적 근거 규칙
  - 트리플렛이 바로 `wiki/ontology/`로 APPEND되어 수동 관계 추출 생략 가능
- `AGENTS.md` · Query 워크플로우:
  - 실행 순서 4번에 **Relevance Scoring** 단계 추가
  - 새 하위 섹션 **Relevance Scoring 프로토콜 (LightRAG Reranker 차용)** — 7개 스코어링 기준, 후보수별 적용 규칙, 투명성 표기 의무
- `README.md`: 버전 1.3.0

**도입 이유:**
- 온톨로지 APPEND 자동화 → Ingest 일관성·속도 향상
- 메타데이터 기반 선별 → 대규모 질의 시 토큰 효율 대폭 절감

---

## [1.2.0] — 2026-04-14

### Lint 유틸리티 스크립트 + 온톨로지 경로 버그 수정

운영 중 축적된 위키 정합성 검사 스크립트 5종을 범용화하여 템플릿에 추가.
SETUP-GUIDE와 README의 ontology 디렉토리 경로 오류를 수정.

**변경사항:**
- `scripts/` 5개 추가:
  - `wiki-stats.py` — 위키 저장소 통계 (페이지/태그/링크/콘텐츠 현황)
  - `find-orphans.py` — 고아 페이지 탐지 (인바운드 링크 0)
  - `check-tags.py` — 태그 프리픽스 준수 검사
  - `scan-broken-links.py` — 깨진 위키링크 스캔
  - `check-ontology.py` — 온톨로지 정합성 검사 (미존재 페이지 참조)
- `AGENTS.md`: Lint 유틸리티 스크립트 섹션 추가, 버전 v1.2.0
- `README.md`: 파일 테이블에 스크립트 5종 추가, 버전 1.2.0
- **Bug fix**: `SETUP-GUIDE.md` Phase 2·3 — `ontology/` → `wiki/ontology/`로 수정
  - mkdir 명령어: `ontology` → `wiki/{...,ontology}` (wiki 하위로 올바르게 생성)
  - cp 명령어: `./ontology/` → `./wiki/ontology/`
  - 디렉토리 구조 다이어그램 수정

---

## [1.1.0] — 2026-04-14

### 2-tier 인덱싱 + 태그 프리픽스 + Smart Diff 도입

PARA Knowledge Base 분석을 반영하여 토큰 효율성과 탐색 성능을 대폭 개선.

**변경사항:**
- `AGENTS.md`:
  - 태그 프리픽스 규칙 추가 (`prod/`, `customer/`, `type/`, `topic/`, `series/`)
  - 자동 위키링크 규칙 명문화 (첫 등장만  링크, 문서당 최대 10개)
  - 5-Route 쿼리 전략 도입 (Direct/Tag/Backlink/Index/FullText)
  - 인덱스 시스템을 2-tier + Smart Diff(3-tier)로 업그레이드
  - Ingest 워크플로우: `_index.md` Tier 1 업데이트 단계 추가
- `starter-files/index.md`: 카테고리 요약 테이블 허브 형식으로 변환
- 스케일 설명에 2-tier 인덱스 참조 추가

**토큰 효율 개선:**
- 질의 시: ~3K → ~200~400 토큰 (80%+ 절감)
- 인덱스 업데이트: ~1500 → ~50 토큰 (Tier 1)

---

## [1.0.0] — 2026-04-12

### 최초 릴리스

Owen의 LLM Wiki 저장소 (197+ 페이지, 8 클러스터, 180+ 온톨로지 관계) 운영 경험을 기반으로 작성.

**포함된 파일:**
- `README.md` — 전체 가이드 (Quick Start, 아키텍처 개요)
- `AGENTS.md` — LLM 에이전트 스키마 (레이어 규칙, 4개 워크플로우, 온톨로지 관계코드)
- `SETUP-GUIDE.md` — 7-Phase 단계별 설정 가이드
- `CHANGELOG.md` — 이 파일

**starter-files/**
- `index.md` — 빈 인덱스 (카테고리 구조만)
- `log.md` — 초기 로그 항목
- `overview.md` — 빈 종합 개요

**templates/** (5종)
- `entity-template.md`
- `concept-template.md`
- `summary-template.md`
- `comparison-template.md`
- `synthesis-template.md`

**ontology-templates/** (6종)
- `entities-ontology.md`
- `concepts-ontology.md`
- `summaries-ontology.md`
- `synthesis-ontology.md`
- `full-wiki-ontology.md`
- `gap-analysis.md`

**scripts/**
- `extract-raw-sources.py` — markitdown 기반 바이너리→마크다운 추출기

### 기반 기술
- Andrej Karpathy의 LLM Wiki 패턴
- Nodus Labs/InfraNodus의 Knowledge Graph 확장
- 온톨로지 그래프 레이어 (증분 업데이트, 클러스터-갭 분석)
- 4개 워크플로우: Ingest, Query, Lint, Ontology Update

---

## 버전 관리 규칙

- **MAJOR** (X.0.0): 아키텍처 레이어 추가/삭제, 워크플로우 근본 변경
- **MINOR** (0.X.0): 새 템플릿 추가, 관계코드 확장, 워크플로우 단계 추가
- **PATCH** (0.0.X): 오타 수정, 설명 개선, 가이드 보강

Owen의 WIKI에서 다음 상황이 발생하면 이 킷을 버전업한다:
1. AGENTS.md의 워크플로우가 변경될 때
2. 새로운 레이어/폴더가 추가될 때
3. 온톨로지 관계코드가 확장될 때
4. 페이지 타입이 추가될 때
5. 스크립트가 업데이트될 때
