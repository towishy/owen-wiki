# LLM Wiki 스키마

> 이 파일은 LLM 에이전트가 위키를 관리할 때 따라야 할 규칙과 컨벤션을 정의한다.
> 사용자와 LLM이 함께 발전시켜 나가는 설정 파일이다.
>
> **Owen-WIKI Template v1.3.0** — {{YOUR_NAME}}의 도메인에 맞게 수정하여 사용.

---

## 볼트 구조

```
{{PROJECT_ROOT}}/
├── AGENTS.md              ← 이 파일 (스키마)
├── index.md               ← 위키 전체 페이지 카탈로그
├── log.md                 ← 시간순 작업 기록
├── raw/                   ← 원본 소스 (불변)
│   ├── assets/            ← 이미지, CSV 등 첨부파일
│   ├── articles/          ← 웹 클리핑 기사
│   ├── papers/            ← 논문
│   ├── notes/             ← 수기 메모, 회의록
│   └── extracted/         ← 바이너리→마크다운 추출 결과
├── wiki/                  ← LLM이 관리하는 위키 페이지 + 온톨로지
│   ├── entities/          ← 인물, 조직, 도구 등
│   ├── concepts/          ← 개념, 이론, 프레임워크
│   ├── summaries/         ← 소스별 요약
│   ├── comparisons/       ← 비교 분석
│   ├── synthesis/         ← 종합 분석, 테마별 정리
│   └── ontology/          ← 온톨로지 그래프 레이어
│       ├── entities-ontology.md     ← entities/ 관계 그래프
│       ├── concepts-ontology.md     ← concepts/ 관계 그래프
│       ├── summaries-ontology.md    ← summaries/ 관계 그래프
│       ├── synthesis-ontology.md    ← synthesis/ 관계 그래프
│       ├── full-wiki-ontology.md    ← 전체 위키 통합 온톨로지
│       └── gap-analysis.md          ← 최근 갭 분석 결과
├── outputs/               ← 최종 산출물 (발표, 보고서, 워크숍 등)
│   ├── presentations/     ← 슬라이드
│   ├── reports/           ← 보고서
│   ├── workshops/         ← 워크숍 자료
│   └── drafts/            ← 작성 중인 산출물
├── scripts/               ← 유틸리티 스크립트
└── templates/             ← 페이지 템플릿
```

---

## 레이어 규칙

### Raw Sources (`raw/`)
- 사용자가 소스를 추가/삭제/정리한다
- 이미지 및 첨부파일은 `raw/assets/`에 저장한다
- 바이너리 파일(PDF/PPTX/DOCX/XLSX)은 `scripts/extract-raw-sources.py`로 마크다운 변환 후 인제스트한다

### Wiki (`wiki/`)
- **LLM 소유**: 모든 생성, 수정, 삭제는 LLM이 수행한다
- 사용자는 읽기만 하며, 수정 요청은 LLM에게 지시한다
- 모든 위키 페이지는 YAML 프론트매터를 포함한다

### Outputs (`outputs/`)
- **공동 소유**: 사용자와 LLM 모두 생성·수정·삭제할 수 있다
- wiki/의 정제된 지식을 특정 청중·목적에 맞게 가공한 최종 산출물을 저장한다
- 완성된 산출물은 하위 폴더에, 작업 중인 것은 `drafts/`에 둔다
- 산출물은 관련 wiki 페이지를 `[[위키링크]]`로 참조한다

### Ontology (`wiki/ontology/`)
- wiki/ 하위 폴더로 통합 — wiki와 동일한 LLM 소유 레이어
- 위키 페이지 간 관계를 `[[위키링크]] [관계코드] [[위키링크]]` 형식으로 기록한다
- 카테고리별 온톨로지 파일 + 전체 통합 온톨로지 + 갭 분석 결과로 구성한다
- **증분 업데이트 원칙**: 절대 전체 재생성하지 않는다. 새 관계만 APPEND, 무효 관계만 제거한다
- 갭 분석 결과는 다음 Ingest/Lint의 우선순위를 결정한다

### Schema (`AGENTS.md`)
- 사용자와 LLM이 공동으로 진화시킨다
- 새로운 컨벤션이 필요하면 이 파일을 업데이트한다

### 지식 파이프라인
```
raw/ (입력) → wiki/ (정제 + 온톨로지) → outputs/ (산출)
                         ↑
                    관계 추출 · 갭 분석
```

---

## 페이지 컨벤션

### YAML 프론트매터 (모든 위키 페이지에 필수)

```yaml
---
title: "페이지 제목"
type: entity | concept | summary | comparison | synthesis
tags: [prod/mde, type/summary, topic/zero-trust, customer/현대자동차]
sources: ["소스 파일 경로"]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

### 태그 프리픽스 규칙

모든 태그는 **접두사/값** 형식을 사용한다. 카테고리 횡단 탐색을 가능하게 한다.

| 접두사 | 용도 | 예시 |
|--------|------|------|
| `prod/` | 제품/도구 | `prod/my-product`, `prod/my-tool` |
| `customer/` | 고객사/조직 | `customer/acme-corp` |
| `type/` | 문서 유형 | `type/summary`, `type/demo`, `type/lab`, `type/webinar`, `type/rca` |
| `topic/` | 주제·기술 영역 | `topic/zero-trust`, `topic/performance` |
| `series/` | 시리즈·프로그램 | `series/training-101` |

**태그 규칙:**
- 한 페이지에 최소 2개, 최대 8개 태그 권장
- `prod/` 태그는 해당 제품 엔티티 페이지명과 일치시킨다
- `customer/` 태그는 고객사 엔티티 페이지명과 일치시킨다
- 중복 없이 가장 구체적인 태그를 사용한다

### 위키링크
- Obsidian 위키링크 사용: `[[페이지명]]`
- 관련 개념/엔티티에는 적극적으로 링크를 건다
- 새로운 개념이 언급되면 해당 페이지를 생성하거나, 생성 예정으로 표시한다

**자동 위키링크 규칙** (ingest 시):
- 문서 내 첫 등장만 링크한다 (동일 용어 반복 링크 금지)
- 코드 블록, URL, YAML 프론트매터 안에서는 링크하지 않는다
- 문서당 최대 10개 자동 링크 (과도한 링크는 노이즈)
- 일반 단어는 동명 페이지가 있어도 링크하지 않는다

### 파일명
- 소문자, 하이픈 구분: `machine-learning.md`, `andrej-karpathy.md`
- 한글 파일명 허용: `강화학습.md`
- 공백 대신 하이픈 사용

---

## 워크플로우

### 1. Ingest (수집)

새 소스가 `raw/`에 추가되면:

1. 소스를 읽고 핵심 내용을 파악한다
2. **트리플렛 추출** — 소스에서 `(주체, 관계, 객체)` 형식의 엔티티-관계 트리플렛을 먼저 구조화하여 추출한다 (아래 트리플렛 추출 프로토콜 참조)
3. `wiki/summaries/`에 요약 페이지를 생성한다 (태그 프리픽스 포함)
4. 추출된 트리플렛을 기반으로 관련 엔티티 페이지를 `wiki/entities/`에서 업데이트하거나 생성한다
5. 추출된 트리플렛을 기반으로 관련 개념 페이지를 `wiki/concepts/`에서 업데이트하거나 생성한다
6. 기존 위키 페이지의 교차참조를 업데이트한다 (자동 위키링크 규칙 적용)
7. 트리플렛을 `wiki/ontology/` 파일에 APPEND한다 (수동 관계 추출 단계 생략 가능)
8. 해당 카테고리의 `_index.md`에 1줄 추가한다 (**Tier 1 인덱싱**)
9. `log.md`에 작업을 기록한다

#### 트리플렛 추출 프로토콜 (LightRAG 차용)

Ingest 시 LLM이 다음 구조화된 형식으로 트리플렛을 먼저 추출한 후 페이지 작성에 활용한다.

**추출 형식:**
```
ENTITIES:
- name: "엔티티명"
  type: person | org | product | tool | customer | concept
  description: "한 줄 설명"

RELATIONS:
- source: "엔티티A"
  relation: 관계코드   # uses, integrates-with, deployed-at, competes-with, related-to, part-of, depends-on 등
  target: "엔티티B"
  evidence: "소스의 근거 문장(요약)"
```

**규칙:**
- 한 소스당 트리플렛 5–20개 권장 (너무 많으면 노이즈, 너무 적으면 추출 부족)
- 모든 트리플렛은 **소스의 명시적 진술**에 근거해야 함 (LLM의 일반 지식으로 추론 금지)
- `evidence` 필드는 갭 분석·검증 시 활용
- 추출된 트리플렛은 그대로 `wiki/ontology/`의 `[[A]] [관계] [[B]]` 형식으로 변환하여 APPEND

### 2. Query (질의)

질문을 받으면 **최적 경로**를 선택한다 (5-Route 전략):

| Route | 조건 | 경로 |
|-------|------|------|
| A. Direct | 특정 엔티티/제품 질문 | `wiki/entities/` 또는 `wiki/concepts/` 직접 접근 |
| B. Tag | 주제 횡단 수집 | `prod/`, `topic/` 태그로 grep 검색 |
| C. Backlink | 참조 탐색 | `[[위키링크]]` grep 또는 온톨로지 |
| D. Index | 전체 현황·시간순 | `_index.md` 또는 `log.md` |
| E. FullText | 키워드 검색 | grep 전체 검색 |

복합 질문은 여러 Route를 조합한다.

**실행 순서:**
1. `index.md` (허브)를 읽어 카테고리 파악 (~20줄, ~50 토큰)
2. 해당 카테고리의 `_index.md`를 읽어 대상 페이지 식별 (~20줄)
3. 필요 시 `wiki/ontology/full-wiki-ontology.md`에서 구조적 관계 확인
4. **Relevance Scoring** — 후보 페이지가 5개 이상이면 아래 스코어링 프로토콜로 상위 N개만 선별한 후 본문을 읽는다
5. 대상 페이지를 읽고 합성 답변 생성
6. 답변에 `[[위키링크]]`로 출처 표시
7. 유용한 답변은 `wiki/`에 새 페이지로 저장
8. `log.md`에 질의 기록

#### Relevance Scoring 프로토콜 (LightRAG Reranker 차용)

복합 질의에서 여러 Route가 다수 후보 페이지를 반환할 때, 본문을 읽기 전에 **메타데이터만으로 점수화**하여 상위 N개만 컨텍스트에 포함한다. 토큰 효율성과 답변 정확도를 동시에 향상.

**스코어링 기준 (각 1점, 합산):**

| 항목 | 점수 | 판단 근거 |
|------|------|---------|
| **제목 일치** | +3 | 질의 키워드가 페이지 `title`에 포함 |
| **태그 일치** | +2 | 질의 의도와 일치하는 `prod/`, `topic/`, `customer/` 태그 보유 |
| **타입 일치** | +2 | 질의가 "비교"면 `comparison`, "개념"이면 `concept` 등 type 일치 |
| **최신성** | +1 | `updated`가 최근 90일 이내 |
| **소스 풍부도** | +1 | `sources` 필드에 3개 이상 |
| **온톨로지 중심성** | +2 | `wiki/ontology/`에서 인바운드 관계 5개 이상 (허브 페이지) |
| **백링크 풍부도** | +1 | 다른 페이지에서 `[[페이지명]]` 참조 3회 이상 |

**적용 규칙:**
- 후보 5개 이하 → 스코어링 생략하고 전부 읽음
- 후보 6–15개 → 상위 5개만 본문 읽음
- 후보 16개 이상 → 상위 7개 + 클러스터 대표 1–2개
- 점수 동률은 `updated`가 최신인 페이지 우선
- 답변 마지막에 "검토한 페이지: N개 / 후보 M개" 표기 (투명성)

**예시:**
```
질의: "고객사 X의 Zero Trust 도입 사례"
→ Route B (tag): customer/X + topic/zero-trust 매칭 12개
→ Scoring: 상위 5개 선별 (고객사 메인 페이지 +9, ZT pillar 페이지 +7, ...)
→ 본문 5개만 읽고 합성
```

### 3. Lint (점검)

주기적으로:

1. 페이지 간 모순을 검사한다
2. 새 소스에 의해 대체된 오래된 주장을 식별한다
3. 인바운드 링크가 없는 고아 페이지를 발견한다
4. 언급되었지만 페이지가 없는 개념을 식별한다
5. 누락된 교차참조를 추가한다
6. 데이터 갭에 대해 추가 소스를 제안한다
7. `wiki/ontology/` 파일을 기반으로 클러스터-갭 분석을 수행한다
8. `wiki/ontology/gap-analysis.md`를 업데이트한다
9. `log.md`에 점검 결과를 기록한다

### 4. Ontology Update (온톨로지 갱신)

대규모 변경(10+ 페이지) 후에:

1. 변경된 페이지들의 `[[위키링크]]`를 추출한다
2. 기존 온톨로지 파일을 읽는다
3. 새 관계만 APPEND, 무효 관계만 제거한다 (절대 전체 재생성 금지)
4. `wiki/ontology/full-wiki-ontology.md`의 카테고리 간 관계를 갱신한다
5. 갭 분석을 재실행하고 `wiki/ontology/gap-analysis.md`를 업데이트한다
6. `wiki/synthesis/overview.md`를 갱신한다
7. `log.md`에 기록한다

---

## 온톨로지 관계코드

| 코드 | 의미 | 예시 |
|------|------|------|
| `[contains]` | 포함/구성 | `[[Platform]] [contains] [[Product]]` |
| `[implements]` | 구현/활용 | `[[Framework]] [implements] [[Tool]]` |
| `[depends-on]` | 의존 | `[[ProductA]] [depends-on] [[ProductB]]` |
| `[deploys]` | 배포/사용 | `[[Customer]] [deploys] [[Product]]` |
| `[supports]` | 지원/호환 | `[[Tool]] [supports] [[Platform]]` |
| `[related-to]` | 관련 | `[[ConceptA]] [related-to] [[ConceptB]]` |
| `[extends]` | 확장/심화 | `[[Basic]] [extends] [[Advanced]]` |
| `[solves]` | 문제 해결 | `[[Guide]] [solves] [[Issue]]` |
| `[teaches]` | 교육/학습 | `[[Course]] [teaches] [[Topic]]` |
| `[competes-with]` | 경쟁 | `[[ProductA]] [competes-with] [[ProductB]]` |

---

## 로그 형식

`log.md`의 각 항목:

```markdown
## [YYYY-MM-DD] 작업유형 | 제목

- 작업 요약
- 영향받은 페이지: [[페이지1]], [[페이지2]]
```

작업유형: `ingest`, `query`, `lint`, `update`, `create`

---

## 인덱스 시스템 (2-tier + Smart Diff)

### 구조
- **`index.md`** (허브): 카테고리별 통계 요약 테이블 + 최근 활동 (~30줄)
- **`wiki/{category}/_index.md`** (카테고리별): 해당 카테고리 전체 페이지 목록 (~10–80줄)
  - `wiki/entities/_index.md`, `wiki/concepts/_index.md`, `wiki/summaries/_index.md`, `wiki/comparisons/_index.md`, `wiki/synthesis/_index.md`

### Smart Diff 인덱싱 (3-tier 전략)

| Tier | 트리거 | 동작 | 토큰 비용 |
|------|--------|------|----------|
| **Tier 1** | Ingest 시 1개 파일 추가 | 해당 `_index.md`에 1줄 APPEND + count 갱신 | ~50 |
| **Tier 2** | 수 개 파일 변경, 인덱스 불일치 의심 | `_index.md`와 실제 파일 diff → 변경분만 편집 | ~200–500 |
| **Tier 3** | 대규모 구조 변경, `--full` | 카테고리별 `_index.md` 전체 재생성 | ~1500–3000 |

**Tier 판별 기준:**
- 파일 1개 추가/삭제 → Tier 1 (ingest가 자동 처리)
- "인덱스 맞나?" / 소수 파일 변경 → Tier 2
- 폴더 구조 대폭 변경 / 30%+ 변경 → Tier 3

### `_index.md` 형식

```yaml
---
title: "{Category} Index"
type: _index
updated: YYYY-MM-DD
count: N
---
```

```markdown
# {Category} — N개

## 하위 분류 (선택)
- [[페이지명]] — 한 줄 설명
```

### `index.md` (허브) 형식

```markdown
| 카테고리 | 페이지 수 | 상세 인덱스 | 허브 토픽 |
|----------|----------|------------|----------|
| Entities | 65 | wiki/entities/_index.md | ... |

## 최근 활동
- [YYYY-MM-DD] 작업유형 — 제목
```

---

## 출력 형식

- **마크다운 페이지**: 기본 출력 형식 (wiki/ 내 모든 페이지)
- **비교 테이블**: 제품/개념 비교 시 테이블 형식 활용
- **Marp 슬라이드**: 프레젠테이션이 필요할 때 Marp 형식으로 생성
- **차트/다이어그램**: Mermaid 다이어그램 또는 matplotlib 코드 블록
- **Canvas**: Obsidian Canvas 형식으로 개념 맵 생성 가능

---

## 바이너리 소스 추출

### 환경 설정

```bash
python3 -m venv .venv
.venv/bin/pip install 'markitdown[pdf,pptx,docx,xlsx]'
```

### 사용법

```bash
.venv/bin/python scripts/extract-raw-sources.py <소스폴더> <출력폴더> [--type pdf|pptx|docx|xlsx|all]
```

### 추출 규칙
- 원본(raw/)은 절대 수정하지 않는다 (불변)
- 추출 결과는 `raw/extracted/` 하위에 원본 폴더 구조를 유지하며 .md로 저장한다

---

## Knowledge Capture 패턴

대화나 미팅 노트에서 지식을 캡처할 때:

1. **분류**: 캡처 유형 결정 (결정사항, How-to, FAQ, 개념, 학습 노트, 문서)
2. **위치**: wiki/ 하위 적절한 카테고리 선택
3. **추출**: 핵심 사실, 결정, 행동 항목, 근거를 구조화
4. **생성**: YAML 프론트매터 + 위키링크 포함하여 페이지 생성
5. **연결**: 관련 페이지에 교차참조 추가, index.md 업데이트

---

## 스케일 & 도구

### 스케일 전환 기준
- 위키 페이지 ~100개까지: 2-tier 인덱스 + wiki/ontology/ 기반 탐색으로 충분
- 위키 페이지 **500+** 이상: 로컬 마크다운 검색 엔진(qmd 등) 도입 권장

### Lint 유틸리티 스크립트

프로젝트 루트에서 실행:

```bash
python scripts/wiki-stats.py          # 위키 통계 (페이지/태그/링크 현황)
python scripts/find-orphans.py         # 고아 페이지 탐지 (0 인바운드 링크)
python scripts/check-tags.py           # 태그 프리픽스 준수 검사
python scripts/scan-broken-links.py    # 깨진 위키링크 스캔
python scripts/check-ontology.py       # 온톨로지 정합성 검사
```

LLM Lint 워크플로우와 병행하여 사용하면 정합성을 더 정밀하게 유지할 수 있다.

### 추천 도구
- **Obsidian**: 마크다운 에디터 + Graph View + 위키링크 네비게이션
  - Web Clipper: 브라우저 기사 → 마크다운 변환
  - Dataview: YAML 프론트매터 기반 동적 테이블
  - Marp Slides: 프레젠테이션 생성
- **Git**: 버전 히스토리, 브랜칭, 롤백

---

## 커스터마이징 가이드

이 스키마를 자신의 도메인에 맞게 수정하려면:

1. `{{PROJECT_ROOT}}`를 실제 경로로 변경
2. `{{YOUR_NAME}}`을 자신의 이름으로 변경
3. raw/ 하위 구조를 자신의 소스 유형에 맞게 조정
4. 관계코드에 도메인 고유 코드를 추가 (예: 의학 위키라면 `[treats]`, `[diagnoses]`)
5. 페이지 타입에 도메인 고유 타입 추가 (예: `question`, `timeline`, `data`)
