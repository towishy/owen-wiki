# Owen-WIKI Template Kit — Changelog

이 파일은 Owen-WIKI 템플릿 킷의 버전 변경 이력을 기록한다.
Owen의 WIKI 저장소가 발전할 때마다 이 킷도 함께 버전업된다.

---

## [1.12.0] — 2026-04-25

### Curation Automation

Action Queue와 relation quality 리포트를 “볼거리”에서 실제 큐레이션 실행 도구로 연결.

**AGENTS.md 변경:**
- `### Curation Automation (v1.12+)` 신규 섹션 추가
- registry source sampling, lifecycle recommendation, synthesis expansion 분리, safe relation rewrite 운영 원칙 명시
- 현재 규모 갱신: 663 pages / 6,317 wikilinks / 600 tags / graph 698 nodes, 3,608 edges

**스크립트 추가/강화:**
- `sample-registry-candidate.py` — registry 후보의 sources에서 대표 3~5개 샘플링 패킷 생성
- `apply-ontology-relation-suggestions.py` — `related-to` 안전 치환 후보를 dry-run/apply로 반영
- `registry-promotion-lifecycle.py` — 후보별 `recommended_status`, `recommendation_reason` 자동 부여
- `wiki-action-queue.py` — 신규 synthesis 후보와 기존 synthesis 확장 후보 분리
- `check-ontology.py` — `synthesizes` relation code를 canonical set에 추가

**운영 결과:**
- safe ontology rewrite 25건 적용: weak `related-to` 172 → 147
- `[[sentinel-operations-overview]]` synthesis 승격 패턴을 템플릿 운영 사례로 반영

---

## [1.11.0] — 2026-04-25

### Operations Precision

Action Queue와 운영 대시보드를 단순 후보 나열에서 “좋은 후보가 위에 뜨는” 운영 정밀도 레이어로 확장.

**AGENTS.md 변경:**
- `### Operations Precision (v1.11+)` 신규 섹션 추가
- generic registry hub 감점, `part-*` dedupe, lifecycle CLI, relation quality, synthesis 승격 운영 원칙 명시

**스크립트 추가/강화:**
- `wiki-action-queue.py` — generic registry hub(`outputs`, `_Templates`, `_MOC`, `misc`) 감점, broad product mix 감점, `part-*` 후보 group dedupe
- `registry-promotion-lifecycle.py` — `--set PAGE status --note ... --target-summary ...` CLI 지원, queue에서 빠진 candidate 자동 deferred 처리
- `wiki-ops-dashboard.py` — 이전 실행 대비 delta와 ontology relation quality 요약 추가
- `check-ontology-relations.py` — 약한 `related-to` 관계를 더 구체적인 relation으로 바꿀 후보 리포트 생성
- `tag-aliases.yml` — 대소문자 drift 태그 alias 추가

**운영 결과:**
- Action Queue tag normalization 후보를 0으로 낮추는 운영 루프 지원
- 큰 synthesis 후보를 curated synthesis로 승격하는 패턴을 정식화

---

## [1.10.0] — 2026-04-25

### Operations Dashboard + Registry Promotion Lifecycle + Query Routing Policy

흩어진 운영 리포트를 단일 진입점으로 묶고, source registry 후보를 curated summary로 승격하는 상태 기반 워크플로우를 추가.

**AGENTS.md 변경:**
- `### Operations Dashboard & Promotion Lifecycle (v1.10+)` 신규 섹션 추가
- registry 승격 상태(`candidate`, `sampled`, `promoted`, `deferred`, `rejected`) 정의
- `### Query Routing Policy (v1.10+)` 신규 섹션 추가
- 질의 응답 시 synthesis/entity/concept/curated summary를 우선하고, source registry는 raw coverage 근거로 후순위 사용하도록 명시

**스크립트 추가/강화:**
- `registry-promotion-lifecycle.py` — Action Queue의 source registry 후보를 상태 기반으로 추적
- `wiki-ops-dashboard.py` — quality gate, action queue, promotion lifecycle, ontology sidecar 핵심 지표를 단일 대시보드로 생성
- `weekly-gap-report.py` — promotion lifecycle과 operations dashboard 실행 결과 포함

**CI 변경:**
- `.github/workflows/wiki-lint.yml`에서 `wiki-ops-dashboard.py` 실행

---

## [1.9.0] — 2026-04-25

### Action Queue + CI Quality Gates

qmd/hybrid search 도입은 제외하고, 기존 graph/tag/source 메타데이터만으로 다음 큐레이션 우선순위를 산출하는 운영 자동화를 추가.

**AGENTS.md 변경:**
- `### Action Queue 운영 (v1.9+)` 신규 섹션 추가
- Raw 지식화 등급(`registered`, `summarized`, `linked`, `synthesized`, `output-used`) 정의
- 주간 운영 주기에 registry 승격 후보, synthesis 후보, tag normalization 후보 포함

**스크립트 추가/강화:**
- `wiki-action-queue.py` — source registry 승격 후보, synthesis 후보, 태그 정규화 후보, raw 지식화 등급, graph/search 랭킹 힌트 생성
- `build-ontology-sidecar.py` — Markdown ontology를 relation weight/evidence/path 포함 JSONL로 변환
- `wiki-quality-gates.py` — broken/orphan/tag/stub/remaining raw parent hub 링크를 CI gate로 강제
- `apply-tag-aliases.py` — `tag-aliases.yml` 기반 태그 alias 실제 적용
- `weekly-gap-report.py` — Action Queue 실행 결과를 주간 리포트에 포함
- `absorb-uningested-subhubs.py` — remaining raw source registry sub-hub 생성
- `find-uningested-raw.py` — 큰따옴표와 파이프(`|`)가 포함된 raw 파일명 매칭 보강

**CI 변경:**
- `.github/workflows/wiki-lint.yml`에서 `wiki-quality-gates.py` 실행
- PR마다 `wiki-action-queue.py`를 생성해 보고서 아티팩트에 포함

---

## [1.8.0] — 2026-04-24

### 저장소 최적화 도구 세트 (분석·자동화 스크립트 8종)

위키 규모가 커질수록 필요한 **건강 점검·분석·자동화** 도구를 정식 패키지화. 본 v1.8.0은 코드 변경만 수반하며 AGENTS.md 워크플로 자체는 v1.7.0과 호환.

**AGENTS.md 변경:**
- `### 저장소 최적화 도구 (v1.8+)` 신규 섹션 추가 (스케일 & 도구 하위)
  - 스크립트 8종 + 강화된 check-ontology.py + tag-aliases.yml + GitHub Actions CI
  - 권장 운영 주기 (PR마다 / 주간 / 월간 / 상시)

**스크립트 추가 (8종):**

| 파일 | 용도 |
|------|------|
| `analyze-large-hubs.py` | 50KB+ 거대 허브 식별 + sub-hub 분할 계획 (sources 클러스터 키 기반) |
| `identify-stubs.py` | stub 페이지 자동 식별 (본문<200자, 무소스 등) → 보강 큐 보고서 |
| `backfill-confidence.py` | confidence/last_confirmed 휴리스틱 백필 (소스 풍부도 + type 기반) |
| `build-raw-to-wiki-map.py` | raw→wiki 역참조 맵 (변환율 측정·고립 raw 식별) |
| `generate-outputs-backlinks.py` | outputs→wiki 백링크 자동 부여 (`<!-- AUTO -->` 마커로 안전 갱신) |
| `compute-pagerank.py` | 그래프 PageRank로 허브 페이지 식별 (NetworkX 의존성 없이 자체 구현) |
| `weekly-gap-report.py` | 주간 갭 분석 종합 (orphans/broken/stubs/decay/raw-coverage 통합) |
| `sync-to-obsidian.ps1` | wiki→외부 Obsidian 볼트 증분 동기 (양 OS 호환 pwsh 7+, `-Destination` 또는 `$env:OBSIDIAN_MIRROR`) |

**기존 스크립트 강화:**
- `check-ontology.py` — supersedes/superseded_by **양방향 일관성 검증** + **31개 표준 관계코드 사전** (uses, integrates-with, deployed-at, ..., teaches, solves)

**신규 설정:**
- `tag-aliases.yml` — 태그 정규화 매핑 사전 (`정규: [별칭, ...]` 형식, `migrate-tags.py`와 결합 사용)
- `.github/workflows/wiki-lint.yml` — PR 시 자동 lint 실행 + 보고서 아티팩트 업로드

**도입 이유:**
- 위키 규모 300+ 페이지에서 거대 허브(>100KB) 출현 → Copilot 컨텍스트 부담·편집 지연 발생
- confidence/last_confirmed 메타데이터를 v1.4부터 권장했으나 기존 페이지 백필 도구 부재
- outputs/와 wiki/ 간 단방향 참조만 존재 → wiki 페이지에서 산출물 추적 불가
- 갭 분석을 매번 수동 실행 → 주간 자동화 필요
- macOS↔Windows 양 OS 환경에서 Obsidian 동기화 hook 부재

**호환성:**
- AGENTS.md v1.7.0과 완전 호환 (워크플로 변경 없음, 도구만 추가)
- Python 3.10+ (휴리스틱·그래프 분석은 표준 라이브러리만 사용, NetworkX 미필수)
- PowerShell Core 7+ (Win/macOS/Linux 동일 동작)

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
