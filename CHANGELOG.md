# Owen-WIKI Template Kit — Changelog

이 파일은 Owen-WIKI 템플릿 킷의 버전 변경 이력을 기록한다.
Owen의 WIKI 저장소가 발전할 때마다 이 킷도 함께 버전업된다.

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
