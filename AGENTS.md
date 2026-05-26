# LLM Wiki 스키마

> 이 파일은 LLM 에이전트가 위키를 관리할 때 따라야 할 규칙과 컨벤션을 정의한다.
> 사용자와 LLM이 함께 발전시켜 나가는 설정 파일이다.

---

## 볼트 구조

```
# Windows: C:\OWEN\Drive\wiki\
# macOS:   /Users/owen/Work/wiki/
.
├── AGENTS.md                  ← 이 파일 (스키마)
├── index.md                   ← 위키 전체 페이지 카탈로그
├── log.md                     ← 시간순 작업 기록
├── README.md / CHANGELOG.md / SOURCES.md
├── raw/                       ← 원본 소스 (불변)
│   ├── articles/  ← **수집 폴더 1**: 웹 클리핑·기사·외부 자료
│   │   └── YYYYMM/  ← 월별 폴더 (직속 신규 파일은 모두 이 안)
│   └── obsidian/  ← Obsidian 볼트 (심볼릭 링크 또는 로컬)
│       ├── Clippings/  ← **수집 폴더 2**: Web Clipper 저장 위치
│       │   └── YYYYMM/  ← 월별 폴더 (직속 신규 파일은 모두 이 안)
│       └── outputs/    ← 최종 산출물 (월별 폴더만)
│           └── YYYYMM/
│               └── attachments/
├── wiki/                      ← LLM이 관리하는 위키 페이지 + 온톨로지
│   ├── entities/  concepts/  summaries/  comparisons/  synthesis/
│   └── ontology/   ← 관계 그래프 레이어
├── outputs/                   ← 호환용 stub → raw/obsidian/outputs (Win: 텍스트 stub / macOS: 심볼릭 링크)
│   └── wiki-ops/              ← 운영 대시보드·메트릭·리포트 산출물
├── scripts/                   ← **모든 유틸리티 스크립트는 여기 또는 하위 폴더에만**
│   └── *.py / *.ps1 / *.sh
├── graphify-out/              ← 위키 그래프 시각화 산출물
├── docs/                      ← 운영 가이드
├── lib/                       ← 외부 라이브러리 자산 (vis.js 등)
└── templates/                 ← 페이지 템플릿
```

> **수집 폴더는 `raw/articles/`, `raw/obsidian/Clippings/` 두 곳뿐이다.** 새 외부 소스(웹 클리핑·기사·짧은 메모·다운로드 자료)는 항상 이 두 폴더의 `YYYYMM/` 하위로만 들어간다. 그 외 `raw/` 하위 폴더(`obsidian/EDE/`, `security-*` 등)는 큐레이션·동기화 영역으로, 수집 워크플로우의 신규 입력 대상이 아니다.

---

## 레이어 규칙

### Raw Sources (`raw/`)
- 사용자가 소스를 추가/삭제/정리한다
- **수집 폴더는 두 곳으로 단순화한다**:
  - `raw/articles/` — 웹 클리핑·기사·짧은 메모·다운로드 자료 (수기 추가)
  - `raw/obsidian/Clippings/` — Obsidian Web Clipper 자동 저장 위치
- 그 외 `raw/` 하위(`obsidian/EDE/`, `obsidian/Security/`, `security-onsite-reports/`, `security-microsoft-documents/` 등)는 큐레이션·동기화 영역이며, 신규 수집 워크플로우의 입력 대상이 아니다
- 바이너리 파일(PDF/PPTX/DOCX/XLSX)은 `scripts/extract-raw-sources.py`로 마크다운 변환 후 인제스트한다

#### 수집 폴더 월별 정책 (필수)
- `raw/articles/`, `raw/obsidian/Clippings/` 직속에는 신규 파일을 두지 않는다. 항상 **`YYYYMM/` 하위**에 생성/이동한다.
- `YYYYMM`은 마크다운이면 frontmatter `created` → `updated`, 그 외 형식이거나 frontmatter가 없으면 파일 mtime의 연·월을 사용한다 (예: 2026년 6월 → `202606/`).
- 대상 월 폴더가 없으면 **자동 생성** 후 그 안에 파일을 만든다.
- 기존 큐레이션 하위 폴더(`articles/azdo-scim-wiki/`, `articles/mslearn/`, `Clippings/attachments/` 등)는 **건드리지 않는다** — 월별 정리 대상이 아니다.
- 직속 파일이 발견되면 다음 스크립트로 일괄 재정리한다:
  - `pwsh ./scripts/organize-collection-by-month.ps1` (articles + Clippings 두 곳 모두 정리)

### Wiki (`wiki/`)
- **LLM 소유**: 모든 생성, 수정, 삭제는 LLM이 수행한다
- 사용자는 읽기만 하며, 수정 요청은 LLM에게 지시한다
- 모든 위키 페이지는 YAML 프론트매터를 포함한다

### Outputs (`raw/obsidian/outputs/`)
- **공동 소유**: 사용자와 LLM 모두 생성·수정·삭제할 수 있다
- wiki/의 정제된 지식을 특정 청중·목적에 맞게 가공한 최종 산출물을 저장한다
- 완성된 산출물과 작업 중인 초안 모두 월별 폴더(`YYYYMM/`) 안에 둔다 — 별도 `drafts/` 폴더는 사용하지 않는다
- 산출물은 관련 wiki 페이지를 `[[위키링크]]`로 참조한다
- **기본 경로**: 모든 신규 산출물은 워크스페이스 루트 기준 **상대경로 `raw/obsidian/outputs/`** 아래에 생성한다. 루트 `outputs/`는 호환용 stub이다 (Win: 텍스트 stub / macOS: 심볼릭 링크).

#### 월별 폴더 정책 (필수)
- `raw/obsidian/outputs/` 직속에는 신규 문서를 두지 않는다. 항상 **`outputs/YYYYMM/` 하위**에 생성한다.
- `YYYYMM`은 문서의 **`created` 프론트매터** 기준 연·월. 프론트매터가 없으면 작성 시점의 연·월을 사용한다 (예: 2026년 6월 작성 → `outputs/202606/`).
- 대상 폴더가 없으면 **자동 생성** 후 그 안에 파일을 만든다. 임의의 다른 위치에 두지 않는다.
- **첨부(이미지·SVG 등)**: 문서가 이미지를 참조하면 같은 월의 **`outputs/YYYYMM/attachments/`** 폴더에 둔다. 문서에서는 상대경로 `attachments/foo.svg` 또는 wikilink `![[foo.svg]]`로 참조한다.
- 직속 파일이 발견되면 다음 스크립트로 일괄 재정리한다:
  - 문서: `pwsh ./scripts/organize-outputs-by-month.ps1` (frontmatter `created` → `updated` → 파일 mtime 우선순위)
  - 첨부: `pwsh ./scripts/organize-outputs-attachments-by-month.ps1` (참조 문서의 월 우선, 미참조 첨부는 mtime)

### Ontology (`wiki/ontology/`)
- wiki/ 하위 폴더로 통합 — wiki와 동일한 LLM 소유 레이어
- 위키 페이지 간 관계를 `[[위키링크]] [관계코드] [[위키링크]]` 형식으로 기록한다
- 카테고리별 온톨로지 파일 + 전체 통합 온톨로지 + 갭 분석 결과로 구성한다
- **증분 업데이트 원칙**: 절대 전체 재생성하지 않는다. 새 관계만 APPEND, 무효 관계만 제거한다
- 갭 분석 결과는 다음 Ingest/Lint의 우선순위를 결정한다
- 상세 설계: [[ontology-graph-layer]]

### Schema (`AGENTS.md`)
- 사용자와 LLM이 공동으로 진화시킨다
- 새로운 컨벤션이 필요하면 이 파일을 업데이트한다

### LLM Agent Behavioral Guardrails (Karpathy-inspired)

LLM이 코딩, 위키 수정, 문서 생성, 스크립트 자동화를 수행할 때는 다음 4가지 행동 기준을 기본값으로 둔다.

| 기준 | 적용 원칙 |
|---|---|
| **가정 노출** | 요구가 여러 방식으로 해석될 수 있으면 범위, 입력, 보안 민감도, 성공 기준을 조용히 정하지 않고 드러낸다. 단, 기존 문맥이 충분히 분명하면 바로 실행한다. |
| **단순성 우선** | 오늘 필요한 최소 구조로 해결한다. 단일 사용 추상화, 미래용 설정, 요청받지 않은 기능은 실제 반복 수요가 생길 때까지 미룬다. |
| **최소 변경** | 변경한 모든 줄이 사용자 요청, 새 소스, 새 관계, 새 검증 기준과 직접 연결되어야 한다. 주변 리팩터, 포맷 변경, 주석 정리는 별도 요청 없이는 하지 않는다. |
| **검증 루프** | 완료를 말하기 전에 가장 가까운 실행 검증을 붙인다. 코드 변경은 테스트/typecheck, 위키 변경은 ontology/tag/quality gate, SVG는 a11y/budget/overflow 검증을 우선한다. |

이 원칙은 Karpathy-inspired coding agent guidelines를 템플릿 킷 수준으로 일반화한 것이다. AGENTS 세부 절차가 더 구체적인 경우에는 AGENTS 절차를 우선하고, 이 표는 판단 기준으로 사용한다.

### 지식 파이프라인
```
raw/ (입력) → wiki/ (정제 + 온톨로지) → raw/obsidian/outputs/ (산출)
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
# --- v1.4.0+ 신뢰도 & 라이프사이클 (선택, 신규 페이지부터 권장) ---
confidence: 0.85           # 0.0~1.0 — 출처 풍부도·검증도 기반
last_confirmed: YYYY-MM-DD # 마지막으로 사실을 검증한 날
stale_after: YYYY-MM-DD    # (선택) 자동 stale 표시 시점
supersedes: [[옛페이지]]    # (선택) 이 페이지가 대체한 옛 페이지
superseded_by: [[새페이지]] # (선택) 이 페이지를 대체한 새 페이지
---
```

**Confidence Scoring 가이드:**

| 값 | 의미 | 적용 예시 |
|----|------|---------|
| 0.95–1.0 | Microsoft 공식 문서 + 직접 검증 | MS Learn 인용 + 실험 검증 |
| 0.80–0.94 | 1차 소스 (공식 블로그, 공식 PPT) | MTUB, Ignite 세션 |
| 0.65–0.79 | 2차 소스 (요약, 번역, 분석) | summaries/, 번역 페이지 |
| 0.40–0.64 | 추정·종합 | 개인 메모, 베타 정보 |
| <0.40 | 미검증·draft | 작성 중 페이지 |

**Last Confirmed / Stale After 규칙:**
- `last_confirmed`는 페이지 본문이 여전히 유효함을 사용자가 재확인한 날짜
- `stale_after` 미지정 시 기본값 = `last_confirmed + 180일`
- 90일 경과 → `aging` 태그 자동 부여 (Relevance Scoring 시 -1)
- 180일 경과 → `stale` 태그 자동 부여 (Relevance Scoring 시 -3, 페이지 상단 경고)

**Supersession 규칙:**
- 새 페이지 생성으로 옛 페이지가 노후화될 때 옛 페이지를 삭제하지 않고 `superseded_by` 필드 추가
- 새 페이지의 `supersedes`에는 옛 페이지 위키링크 기록
- 산출물(outputs/)에서 `[[옛페이지]]` 참조 시 LLM이 자동으로 신버전 권장
- 온톨로지 관계: `[[A]] [supersedes] [[B]]`

### 태그 프리픽스 규칙

모든 태그는 **접두사/값** 형식을 사용한다. 카테고리 횡단 탐색을 가능하게 한다.

| 접두사 | 용도 | 예시 |
|--------|------|------|
| `prod/` | Microsoft 보안 제품 | `prod/mde`, `prod/sentinel`, `prod/entra`, `prod/purview-dlp` |
| `customer/` | 고객사 | `customer/현대자동차`, `customer/크래프톤` |
| `type/` | 문서 유형 | `type/summary`, `type/demo`, `type/ninja`, `type/school`, `type/mslearn`, `type/webinar`, `type/lab`, `type/rca` |
| `topic/` | 주제·기술 영역 | `topic/zero-trust`, `topic/identity`, `topic/cloud-security`, `topic/kql` |
| `series/` | 시리즈·프로그램 | `series/zt-pillars`, `series/ninja-training`, `series/security-school` |

**태그 규칙:**
- 한 페이지에 최소 2개, 최대 8개 태그 권장
- `prod/` 태그는 해당 제품 엔티티 페이지명과 일치시킨다
- `customer/` 태그는 고객사 엔티티 페이지명과 일치시킨다
- 중복 없이 가장 구체적인 태그를 사용한다 (예: `prod/mde`만 사용, `prod/microsoft` 불필요)

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

0. **PII 사전 점검** — `scripts/sanitize-ingest.py <파일>` 으로 이메일·IP·토큰·GUID 검사. 발견 시 사용자에게 알리고 마스킹 또는 제외 결정.
1. 소스를 읽고 핵심 내용을 파악한다
2. **트리플릿 추출** — 소스에서 `(주체, 관계, 객체)` 형식의 엔티티-관계 트리플릿을 먼저 구조화하여 추출한다 (아래 트리플릿 추출 프로토콜 참조)
3. `wiki/summaries/`에 요약 페이지를 생성한다 (태그 프리픽스 포함, `confidence` 필드 포함)
4. 추출된 트리플릿을 기반으로 관련 엔티티 페이지를 `wiki/entities/`에서 업데이트하거나 생성한다
5. 추출된 트리플릿을 기반으로 관련 개념 페이지를 `wiki/concepts/`에서 업데이트하거나 생성한다
6. 기존 위키 페이지의 교차참조를 업데이트한다 (자동 위키링크 규칙 적용)
7. 새 소스가 기존 페이지를 대체하는 경우 `superseded_by`/`supersedes` 프론트매터를 기록한다
8. 트리플릿을 `wiki/ontology/` 파일에 APPEND한다 (수동 관계 추출 단계 생략 가능)
9. 해당 카테고리의 `_index.md`에 1줄 추가한다 (**Tier 1 인덱싱**)
10. `log.md`에 작업을 기록한다

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
  relation: 관계코드   # uses, integrates-with, deployed-at, competes-with, related-to, part-of, depends-on, supersedes, superseded-by 등
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
| **신뢰도** | +2 | `confidence ≥ 0.85` (1차 소스 + 검증) / +1 (`≥ 0.65`) |
| **최신성** | +1 | `updated`가 최근 90일 이내 |
| **노후 페널티** | −1 / −3 | `aging` 태그 / `stale` 태그 또는 `superseded_by` 존재 |
| **소스 풍부도** | +1 | `sources` 필드에 3개 이상 |
| **온톨로지 중심성** | +2 | `wiki/ontology/`에서 인바운드 관계 5개 이상 (허브 페이지) |
| **백링크 풍부도** | +1 | 다른 페이지에서 `[[페이지명]]` 참조 3회 이상 |

**적용 규칙:**
- 후보 5개 이하 → 스코어링 생략하고 전부 읽음
- 후보 6–15개 → 상위 5개만 본문 읽음
- 후보 16개 이상 → 상위 7개 + 클러스터 대표 1–2개
- 점수 동률은 `updated`가 최신인 페이지 우선
- `superseded_by` 보유 페이지는 스코어 무관 후순위, 답변에 신버전 페이지 권장
- 답변 마지막에 "검토한 페이지: N개 / 후보 M개" 표기 (투명성)

**예시:**
```
질의: "현대자동차 Zero Trust 도입 사례"
→ Route B (tag): customer/현대자동차 + topic/zero-trust 매칭 12개
→ Scoring: 상위 5개 선별 (현대자동차 메인 페이지 +9, ZT pillar 페이지 +7, ...)
→ 본문 5개만 읽고 합성
```

### 3. Lint (점검)

주기적으로:

1. 페이지 간 모순을 검사한다
2. 새 소스에 의해 대체된 오래된 주장을 식별한다 — `superseded_by` 필드로 명시적 대체 처리
3. 인바운드 링크가 없는 고아 페이지를 발견한다
4. 언급되었지만 페이지가 없는 개념을 식별한다
5. 누락된 교차참조를 추가한다
6. 데이터 갭에 대해 추가 소스를 제안한다
7. **노후 페이지 점검** — `scripts/check-confidence-decay.py` 실행하여 `aging`/`stale` 태그 자동 부여
8. **PII 사전 점검** — Ingest 전 `scripts/sanitize-ingest.py`로 raw/ 신규 파일 검사
9. `wiki/ontology/` 파일을 기반으로 클러스터-갭 분석을 수행한다
10. `wiki/ontology/gap-analysis.md`를 업데이트한다
11. `log.md`에 점검 결과를 기록한다

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

## 로그 형식

`log.md`의 각 항목은 다음 형식을 따른다:

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

질의 응답 및 위키 페이지는 마크다운이 기본이지만, 필요에 따라 다양한 형식을 사용할 수 있다:

- **마크다운 페이지**: 기본 출력 형식 (wiki/ 내 모든 페이지)
- **비교 테이블**: 제품/개념 비교 시 테이블 형식 활용
- **Marp 슬라이드**: 프레젠테이션이 필요할 때 Marp 형식 마크다운 생성 (Obsidian Marp 플러그인 활용)
- **PPTX 프레젠테이션**: `python-pptx` 또는 `pptxgenjs`로 네이티브 PowerPoint 생성 (`raw/obsidian/outputs/YYYYMM/`)
- **DOCX 보고서**: `docx-js`로 Word 문서 생성 (`raw/obsidian/outputs/YYYYMM/`)
- **XLSX 분석**: `openpyxl`/`pandas`로 스프레드시트 생성·분석
- **차트/다이어그램**: SVG 이미지를 우선 생성하고, SVG를 사용할 수 없는 경우에만 Mermaid 또는 matplotlib 코드 블록으로 시각화
- **Canvas**: Obsidian Canvas 형식으로 개념 맵 생성 가능

---

## 다이어그램 표준 (SVG 우선)

모든 도식·인포그래픽은 **SVG 이미지**를 우선 사용한다. SVG를 사용할 수 없는 상황에서만 Mermaid를 fallback으로 사용한다. ASCII 박스 다이어그램은 금지한다.

### SVG 디자인 원칙

- 문서용 SVG는 **고급스럽게 정돈된 정보 구조**를 목표로 한다. 한 SVG의 핵심 메시지는 1개로 제한하고, 시선 흐름은 좌→우, 상→하, 중심→주변 중 하나로 통일한다.
- Owen Graphite 톤에 맞춰 **Liquid Glass 디자인 + 그림자 효과**를 적극 적용한다. 반투명 glass surface, radial highlight, inset shine, 얇은 rim border, 부드러운 drop shadow를 기본 재질로 사용한다.
- 색상은 역할 기반으로 제한한다. neutral/primary/success/warning/risk/insight 중 필요한 3~5개만 사용하고, 의미 없는 다색 장식은 피한다.
- SVG 외곽과 주요 요소 사이에는 최소 48px, 권장 64px 이상의 safe margin을 둔다.
- 카드·패널·배지 내부 요소는 보더에 붙지 않게 최소 20px, 권장 24px 이상의 internal padding을 둔다.
- 텍스트는 절대 박스·라운드·배지 경계 밖으로 튀어나오면 안 된다. 라벨 글자수와 줄 수를 기준으로 박스 폭·높이·radius를 먼저 산정한다.
- 모든 SVG는 `viewBox`, `preserveAspectRatio`, 충분한 대비, 외부 폰트 의존 최소화, light/dark/PDF 식별성을 고려해 작성한다.
- SVG 아래에는 짧은 caption 또는 source note를 두어 그림의 의미와 근거를 설명한다.

### Mermaid fallback 기준

Mermaid는 다음 상황에서만 사용한다.

- 빠른 초안 또는 회의 중 즉석 구조화가 필요한 경우
- Obsidian 원문 안에서 텍스트 기반으로 간단한 흐름을 유지해야 하는 경우
- SVG 파일 생성이 불가능하거나 사용자가 Mermaid를 명시적으로 요청한 경우
- 매우 단순한 플로우/시퀀스라서 SVG 제작 비용이 설명 가치보다 큰 경우

### A3 PDF 가로폭 제한

- SVG 가로 다이어그램은 한 줄 노드 4~5개 이하를 권장하고, Mermaid fallback의 `flowchart LR`은 노드 6개 이하로 제한
- 노드가 많으면 `flowchart TB` 세로 방향 또는 wrap (subgraph 상하 적층)
- Gantt는 일자 단위(7~14일)로 짧게 구성
- 노드 텍스트도 짧게 (`<br/>` 줄바꿈 활용)
- edge label에 `<br/>` 사용 금지 → `"..."` 따옴표로 감싸고 공백으로 구분

### 표준 4색 팔레트 (일반 흐름도)

| 구분 | Fill | Stroke | Text | 용도 |
|------|------|--------|------|------|
| **General** | `#F9FAFB` | `#D1D5DB` | `#1F2937` | 시작/일반 노드 |
| **Highlight** | `#E0F2FE` | `#0EA5E9` | `#075985` | 핵심·강조 |
| **Decision** | `#FFFFFF` | `#6B7280` | `#374151` | 판단 (마름모) |
| **Success** | `#FFFFFF` | `#10B981` | `#065F46` | 최종/완료 |

적용 예시:
```
style MyNode fill:#E0F2FE,stroke:#0EA5E9,color:#075985
```

### 확장 5색 팔레트 (용도별 선택)

표준 4색이 부족할 때(5+ 카테고리, 다단계 절차, 강한 대비 필요) 아래 3종 5색 팔레트 중 하나를 선택해 사용한다. 전체 정의·샘플은 [outputs/wiki-ops/references/mermaid-warm-pastel-palette-sample.md](outputs/wiki-ops/references/mermaid-warm-pastel-palette-sample.md) 참조.

| 팔레트 | 5색 구성 | 적합 용도 |
|--------|---------|---------|
| **Warm Pastel** | Base / Action / Highlight / Critical / Done | 운영 절차, FAQ, 정책 흐름, 사용자 가이드 |
| **Cool Tech** | Start / Tech A / Tech B / Warning / Success | 아키텍처 다이어그램, 기술 통합 흐름, ZT 모델 |
| **Process Steps** | Step 1 / Step 2 / Step 3 / Alert / Final | 단계형 절차, 인시던트 응답, 컴플라이언스 |

**선택 규칙:**
- 카테고리 5종 이상 또는 Critical/Warning 강조 필요 → 확장 5색 팔레트
- Microsoft 제품 식별이 핵심 → 제품별 식별 색상 (아래 표)
- 그 외 일반 흐름 → 표준 4색 (General/Highlight/Decision/Success)
- 한 다이어그램 내에서 표준 4색과 확장 5색을 **혼용하지 않는다**
- `classDef` 형식으로 정의하여 동일 카테고리 노드는 일괄 적용 (style 단건 반복 금지)

### ML Pipeline 8색 팔레트 (역할 기반 다중 카테고리)

6색 이상의 역할 구분이 필요한 파이프라인·분기 다이어그램에 사용한다 (ML 워크플로우, 의사결정 트리, 다중 분기 비교 등). 표준 4색·확장 5색·제품별 색상과 혼용하지 않는다.

| Class | Fill | Stroke | 역할 |
|-------|------|--------|------|
| `prep`   | `#f4f4f9` | `#4c4c4c` | 입력/준비/시작 |
| `train`  | `#d6eaf8` | `#2980b9` | 학습/처리/주요 작업 |
| `eval`   | `#e8f8f5` | `#1abc9c` | 평가/검증/분석 |
| `rf`     | `#f9ebea` | `#e74c3c` | 강조 A · 위험 · 카테고리 1 |
| `gb`     | `#fcf3cf` | `#f39c12` | 강조 B · 주의 · 카테고리 2 |
| `svm`    | `#ebdef0` | `#9b59b6` | 강조 C · 보조 · 카테고리 3 |
| `select` | `#f4f4f9` | `#4c4c4c` | 분기/판단 (마름모) |
| `deploy` | `#d5dbdb` | `#7f8c8d` | 최종/배포/완료 |

적용 예시:
```
classDef prep  fill:#f4f4f9,stroke:#4c4c4c,stroke-width:1px
classDef train fill:#d6eaf8,stroke:#2980b9,stroke-width:1px
A[Data Prep]:::prep --> B[Training]:::train
```

샘플: [outputs/wiki-ops/references/mermaid-ml-pipeline-palette-sample.md](outputs/wiki-ops/references/mermaid-ml-pipeline-palette-sample.md)

### 제품별 식별 색상 (필요 시만)

Microsoft 제품을 시각적으로 구분해야 하는 다이어그램에만 제한적으로 사용:

| 제품 | Fill | Stroke |
|------|------|--------|
| Entra ID P2 | `#efe7ff` | `#bc8cff` |
| MDI | `#fff5d1` | `#d29922` |
| MDE | `#ffe1de` | `#f85149` |
| Intune | `#ffe1f0` | `#f778ba` |
| Purview DLP | `#e1f5e1` | `#3fb950` |
| GSA | `#e1eeff` | `#58a6ff` |
| Conditional Access | `#d1f0ee` | `#39d2c0` |

텍스트 색은 `color:#1a1a1a` (A3 인쇄 친화).

---

## 바이너리 소스 추출

raw/ 폴더의 바이너리 파일(PDF, PPTX, DOCX, XLSX)을 마크다운으로 변환하는 통합 스크립트.
**markitdown**(microsoft/markitdown, 102k⭐)을 1차 엔진으로, pymupdf/python-pptx 등을 폴백으로 사용한다.

### 환경 설정

```bash
# Python 3.12 venv (markitdown은 Python 3.10+ 필요)
.venv/bin/python -c "import markitdown; print('OK')"

# venv가 없으면 생성
python3.12 -m venv .venv
.venv/bin/pip install 'markitdown[pdf,pptx,docx,xlsx]'
```

### 사용법

```bash
# markitdown 엔진 사용 (권장)
.venv/bin/python scripts/extract-raw-sources.py <소스폴더> <출력폴더> [--type pdf|pptx|docx|xlsx|all]

# 예시: onsite-reports의 PPTX 전부 추출
.venv/bin/python scripts/extract-raw-sources.py raw/security-onsite-reports raw/extracted/onsite-reports --type pptx

# 예시: microsoft-documents 전체 추출
.venv/bin/python scripts/extract-raw-sources.py raw/security-microsoft-documents raw/extracted/microsoft-documents --type all

# dry-run으로 대상만 확인
.venv/bin/python scripts/extract-raw-sources.py raw/security-onsite-reports raw/extracted/onsite-reports --dry-run

# 폴백 전용 (markitdown 없는 환경)
python3 scripts/extract-raw-sources.py raw/security-onsite-reports raw/extracted/onsite-reports --no-markitdown
```

### 추출 라이브러리

| 엔진 | 라이브러리 | 용도 | 비고 |
|------|-----------|------|------|
| **1차** | `markitdown` (microsoft/markitdown) | PDF, PPTX, DOCX, XLSX + HTML/CSV/JSON/XML/이미지/오디오/ZIP | Python 3.10+, `.venv` 필요 |
| 폴백 | `pymupdf (fitz)` | PDF 텍스트 추출 | OCR 없이도 대부분 처리 |
| 폴백 | `python-pptx` | PPTX 슬라이드별 텍스트 + 발표자 노트 | |
| 폴백 | `zipfile + xml` | DOCX 문단별 텍스트 | 의존성 최소화 |
| 폴백 | `openpyxl` | XLSX 시트별 마크다운 테이블 | |

### 추출 규칙
- 원본(raw/)은 절대 수정하지 않는다 (불변)
- 추출 결과는 `raw/extracted/` 하위에 원본 폴더 구조를 유지하며 .md로 저장한다
- `--force` 없으면 기존 추출 파일은 건너뛴다
- 추출된 마크다운은 인제스트 파이프라인의 입력으로 사용한다

### Knowledge Capture 패턴 (Notion 스킬 참조)

대화나 미팅 노트에서 지식을 캡처할 때의 워크플로우:

1. **분류**: 캡처 유형 결정 (결정사항, How-to, FAQ, 개념, 학습 노트, 문서)
2. **위치**: wiki/ 하위 적절한 카테고리 선택 (entities/concepts/summaries/synthesis)
3. **추출**: 핵심 사실, 결정, 행동 항목, 근거를 구조화
4. **생성**: YAML 프론트매터 + 위키링크 포함하여 페이지 생성
5. **연결**: 관련 페이지에 교차참조 추가, index.md 업데이트

---

## 스케일 & 도구

### 현재 규모 (2026-05-22, v1.16.0)
<!-- wiki-metrics:agents:start -->
- raw/ 전체: 5,902 파일 (canonical scan 기준)
- wiki/ 페이지: **702**
- 위키링크: 7,451개 (페이지당 평균 10.6)
- 온톨로지 관계: 740개 (v1.16.0 temporal sidecar 기준)
- **raw episode ledger**: 10,097 episodes (`outputs/wiki-ops/episode-ledger.jsonl`)
- Microsoft Security 제품 커버리지: **27/27 (100%)**
- 태그: 651종
- Confidence 분포: 0.95+ 2 / 0.80–0.94 81 / 0.65–0.79 265 / 0.40–0.64 314 / unset 0
- 2-tier 인덱스: `index.md` (허브) + 카테고리별 `_index.md` 6개 (entities/concepts/summaries/comparisons/synthesis/ontology)
- Git 커밋: 170개+ / 작업 로그 라인: 1,350+
- 그래프(graphify-out): 노드 674 · 엣지 3,645 · 커뮤니티 9 · 고아 0 · 깨진 링크 0
- Canonical 운영 지표: `outputs/wiki-ops/wiki-ops-dashboard.json`, 저장소 규모 지표: `outputs/wiki-ops/repo-metrics.json`
- index.md 허브 → 카테고리 _index.md → wiki/ontology/ 기반 구조 분석을 병행한다
<!-- wiki-metrics:agents:end -->

### 자동 클러스터 허브 정책 (v1.7+)
대량 raw/ 자료(고객사별 동일 워크숍 사본 등)는 개별 ingest 대신 **클러스터 허브 페이지**로 일괄 sources 등록한다.
- **임계값**: 3개 이상 파일이 동일 클러스터 키(2~3 단계 경로) 공유 시 허브 자동 생성
- **스크립트**: `scripts/auto-cluster-hubs.py` (자동 생성) + `scripts/absorb-remaining-uningested.py` (잔여 라우팅) + `scripts/absorb-uningested-subhubs.py` (remaining raw sub-hub 수집)
- **confidence**: 자동 허브는 0.55, 큐레이션 허브는 0.65, 1차 소스 summary는 0.85+
- **본문**: 허브는 sources YAML과 클러스터 설명만 작성, 본문 큐레이션은 가치 평가 후 별도 summary로 승격
- **SKIP 패턴**: 이미 인제스트된 클러스터(`raw/articles/mslearn/`, `raw/obsidian/` 등)는 `SKIP_PREFIX`/`SKIP_CONTAINS`로 제외
- **scanner 매칭 규칙** (`scripts/find-uningested-raw.py`): NFC normalize + 괄호·대괄호·작은따옴표·큰따옴표·파이프(`|`) 포함 파일명 지원 필수

### 저장소 최적화 도구 (v1.8+)

규모가 커진 위키의 건강을 유지하기 위한 분석·자동화 스크립트 세트.

| 스크립트 | 용도 | 출력 |
|---------|------|------|
| `scripts/analyze-large-hubs.py` | 50KB+ 거대 허브 식별 + sub-hub 분할 계획 | `outputs/wiki-ops/large-hubs-split-plan.md` |
| `scripts/identify-stubs.py` | stub 페이지 자동 식별 (본문<200자, 무소스 등) | `outputs/wiki-ops/stub-pages-report.md` |
| `scripts/backfill-confidence.py` | confidence/last_confirmed 휴리스틱 백필 | YAML 프론트매터 인플레이스 |
| `scripts/build-raw-to-wiki-map.py` | raw→wiki 역참조 맵 (변환율·고립 raw 식별) | `outputs/wiki-ops/raw-to-wiki-map.{json,md}` |
| `scripts/build-episode-ledger.py` | Graphiti식 raw episode ledger 생성 (stable episode ID, source fingerprint, derived wiki/ontology lineage) | `outputs/wiki-ops/episode-ledger.{jsonl,md}` |
| `scripts/wiki-action-queue.py` | registry 승격·synthesis 후보·태그 정규화·raw 지식화 등급·검색 랭킹 힌트 산출 | `outputs/wiki-ops/wiki-action-queue.{md,json}` |
| `scripts/registry-promotion-lifecycle.py` | source registry 승격 후보의 candidate/sampled/promoted/deferred/rejected 상태 추적 | `outputs/wiki-ops/registry-promotion-lifecycle.{md,json}` |
| `scripts/registry-promotion-workbench.py` | registry 승격 후보별 review packet 생성 | `outputs/wiki-ops/registry-promotion-workbench.{md,json}` |
| `scripts/sample-registry-candidate.py` | registry 후보 sources 대표 3~5개 샘플링 패킷 생성 | `outputs/wiki-ops/registry-samples/` |
| `scripts/wiki-ops-dashboard.py` | quality gate·action queue·promotion lifecycle·ontology sidecar·episode ledger 핵심 지표 단일 대시보드 생성 | `outputs/wiki-ops/wiki-ops-dashboard.{md,json}` |
| `scripts/build-ontology-sidecar.py` | 온톨로지 관계를 JSONL sidecar로 변환 (weight/evidence/path/confidence/temporal/provenance 포함) | `outputs/wiki-ops/ontology-sidecar.{jsonl,md}` |
| `scripts/check-ontology-relations.py` | 약한 `related-to` 관계를 더 구체적 relation으로 치환할 후보 산출 | `outputs/wiki-ops/ontology-relation-quality.{md,json}` |
| `scripts/apply-ontology-relation-suggestions.py` | 검토된 안전 후보를 dry-run/apply로 ontology 파일에 반영 | `outputs/wiki-ops/ontology-relation-rewrite-plan.md` |
| `scripts/generate-outputs-backlinks.py` | outputs→wiki 백링크 자동 부여 (`## 파생 산출물`) | wiki 페이지 인플레이스 |
| `scripts/compute-pagerank.py` | Raw PageRank + query-adjusted rank로 허브/질의 후보 식별 | `outputs/wiki-ops/wiki-pagerank.md` |
| `scripts/wiki-query.py` | Query-adjusted PageRank·태그·본문·온톨로지 기반 후보 페이지 라우팅 | stdout / `outputs/wiki-ops/query-runs/` |
| `scripts/check-graph-hygiene.py` | placeholder/unknown/trailing wikilink로 인한 graph node 오염 탐지 | `outputs/wiki-ops/graph-hygiene.{md,json}` |
| `scripts/check-related-to-budget.py` | weak `related-to` relation 예산 강제 | stdout / CI exit code |
| `scripts/update-metrics-snippets.py` | README/AGENTS의 canonical metrics block 자동 갱신 | README.md / AGENTS.md |
| `scripts/graph-delta-report.py` | Git ref 대비 graph node/edge/degree 변화 리포트 | `outputs/wiki-ops/graph-delta.{md,json}` |
| `scripts/release-wiki.py` | 검증·metrics snippet update·commit·tag·push·GitHub Release 자동화 | git / GitHub Release |
| `scripts/weekly-gap-report.py` | 주간 갭 분석 종합 (orphans/broken/stubs/decay) | `outputs/wiki-ops/weekly-gaps-YYYY-MM-DD.md` |
| `scripts/wiki-quality-gates.py` | CI 품질 게이트 (broken/orphan/tag/stub/registry parent hub) | stdout / exit code |
| `scripts/sync-to-obsidian.ps1` | wiki→Obsidian 볼트 증분 동기 (양 OS pwsh 7+) | 파일 복사 |
| `scripts/check-ontology.py` (강화) | 양방향 supersession 검증 + 표준 관계코드 사전 | stdout |
| `scripts/tag-aliases.yml` | 태그 정규화 매핑 사전 | 데이터 |
| `scripts/apply-tag-aliases.py` | `tag-aliases.yml` 기반 태그 alias 실제 적용 | wiki 페이지 인플레이스 |
| `.github/workflows/wiki-lint.yml` | PR 시 lint 자동 실행 + 보고서 아티팩트 업로드 | GitHub Actions |

**권장 운영 주기:**
- **PR마다**: GitHub Actions로 자동 (orphans / broken-links / ontology / tags / stubs / decay / quality-gates / action-queue / ops-dashboard)
- **주간**: `weekly-gap-report.py` cron/Task Scheduler 등록 → 갭 우선순위 + registry 승격 후보 + synthesis 후보 + promotion lifecycle 결정
- **월간**: `analyze-large-hubs.py` + `compute-pagerank.py`로 구조 점검
- **상시**: `sync-to-obsidian.ps1`을 wiki/ 변경 hook으로 등록

### Action Queue 운영 (v1.9+)

`scripts/wiki-action-queue.py`는 lint가 통과한 상태에서 다음 큐레이션 우선순위를 산출한다. qmd/hybrid search 도입 전에도 기존 graph/tag/source 메타데이터만으로 운영 가능하다.

| Queue | 판단 기준 | 다음 액션 |
|-------|----------|----------|
| Source Registry 승격 후보 | `type/source-registry` + source 수 + 제품/고객/워크숍 키워드 | 고가치 파일 샘플링 후 curated summary 생성 |
| Synthesis 후보 | summary 페이지의 `prod/`, `topic/`, `customer/` 태그 밀도 | 종합 페이지 생성 또는 기존 synthesis 보강 |
| 태그 정규화 후보 | `tag-aliases.yml` 별칭 + 유사 topic spelling | alias 추가 후 `migrate-tags.py` 적용 |
| Raw 지식화 등급 | registered / summarized / linked / synthesized / output-used | registered-only 그룹을 summary 승격 후보로 처리 |
| Graph/Search 랭킹 힌트 | high-degree source registry hub | 질의 rerank에서 downrank 또는 필터 토글 |
| Ontology Sidecar | `[[A]] [관계] [[B]]` + page metadata | relation weight 기반 검색/랭킹/검증 입력 |

**Raw 지식화 등급:**
- `registered`: source registry에만 등록됨
- `summarized`: curated summary에서 인용됨
- `linked`: entity/concept까지 연결됨
- `synthesized`: synthesis 레이어에서 활용됨
- `output-used`: outputs 산출물에서 참조된 wiki 페이지의 source로 활용됨

### Operations Dashboard & Promotion Lifecycle (v1.10+)

`scripts/wiki-ops-dashboard.py`는 흩어진 운영 리포트의 핵심 지표를 단일 진입점(`outputs/wiki-ops/wiki-ops-dashboard.md`)으로 묶는다. 대시보드는 quality gate, Action Queue, registry promotion lifecycle, ontology sidecar, episode ledger를 함께 보여준다.

`scripts/registry-promotion-lifecycle.py`는 Action Queue의 source registry 승격 후보를 상태 기반으로 관리한다.

| Status | 의미 | 다음 액션 |
|--------|------|----------|
| `candidate` | Action Queue에서 자동 선별된 후보 | sources 대표 파일 3~5개 샘플링 |
| `sampled` | 원본 샘플링 중 | curated summary 가치 판단 |
| `promoted` | summary/entity/concept/synthesis 승격 완료 | `target_summary` 기록 |
| `deferred` | 중복·저가치·시기상조로 보류 | `decision_note` 기록 |
| `rejected` | 재검토 가치 낮음 | 근거와 함께 제외 |

### Query Routing Policy (v1.10+)

질의 응답 시 페이지 우선순위는 다음 순서를 따른다.

1. `wiki/synthesis/` — 종합 판단·전략·교차 주제 답변의 1차 근거
2. `wiki/entities/`, `wiki/concepts/` — 특정 제품·고객·개념의 canonical facts
3. curated `wiki/summaries/` — 소스 기반 세부 근거
4. `wiki/comparisons/` — 비교 질의의 직접 근거
5. `type/source-registry` 또는 `remaining-raw-*` — raw coverage 증명·추가 조사 후보로만 사용

Registry-only 페이지는 기본적으로 답변 본문 근거에서 후순위로 둔다. 단, 사용자가 raw coverage, 미수집 여부, 원본 위치, 승격 후보를 묻는 경우에는 직접 근거로 사용할 수 있다. Registry-only 페이지를 사용한 경우 답변에 “원본 등록 근거이며 curated summary는 아님”을 명시한다.

### Operations Precision (v1.11+)

운영 대시보드는 단순 현황 표시를 넘어 다음 정밀도 신호를 함께 제공한다.

- Action Queue는 generic registry hub(`outputs`, `_Templates`, `_MOC`, `misc`)와 broad product mix 후보를 감점하고, `part-*` registry 후보를 그룹 단위로 dedupe한다.
- Registry promotion lifecycle은 `--set PAGE status --note ... --target-summary ...` CLI로 상태를 갱신할 수 있다.
- Tag normalization은 `tag-aliases.yml` + `apply-tag-aliases.py`로 반복 적용하며, Action Queue의 태그 후보 0개를 목표 상태로 둔다.
- Ontology relation quality는 `check-ontology-relations.py`로 약한 `related-to` 관계를 `covers`, `aggregates`, `uses` 등 더 구체적인 relation으로 바꿀 후보를 제안한다.
- 큰 synthesis 후보는 Action Queue에서 확인되는 즉시 curated synthesis로 승격하고, 필요한 경우 `raw/obsidian/outputs/YYYYMM/`에 보고서 사본을 둔다.

### Curation Automation (v1.12+)

운영 정밀도 결과를 실제 큐레이션 행동으로 연결하기 위해 다음 자동화 루프를 사용한다.

- `sample-registry-candidate.py`는 registry 후보의 `sources`에서 제품/고객/워크숍 신호가 강한 대표 파일 3~5개를 `outputs/wiki-ops/registry-samples/`에 샘플링한다.
- `registry-promotion-lifecycle.py`는 각 후보에 `recommended_status`와 `recommendation_reason`을 부여해 `sampled`/`deferred` 판단을 먼저 제안한다.
- `wiki-action-queue.py`는 신규 synthesis 후보와 기존 synthesis 확장 후보를 분리해, 이미 대표 synthesis가 있는 큰 태그를 “신규 생성”이 아니라 “기존 보강”으로 다룬다.
- `apply-ontology-relation-suggestions.py`는 `check-ontology-relations.py` 결과 중 canonical relation으로 안전하게 치환 가능한 `related-to`만 dry-run 후 적용한다.
- 제품별 대형 synthesis 후보는 포트폴리오 → 제품 운영 가이드 순서로 승격한다. 예: [[microsoft-security-portfolio-overview]] 다음 [[sentinel-operations-overview]].

### Ontology Relation Refinement (v1.13+)

온톨로지 품질 루프는 `related-to`를 장기적으로 줄이고, 검색·랭킹·갭 분석에 의미 있는 canonical relation을 늘리는 것을 목표로 한다.

- sidecar는 실제 온톨로지 relation 라인으로 시작하는 `[[A]] [relation] [[B]]`만 집계하며, 후보 표나 설명용 예시는 relation count에서 제외한다.
- relation rewrite는 `outputs/wiki-ops/ontology-relation-quality.md`의 후보를 그대로 적용하지 않고, 대상 페이지 본문 근거를 확인한 뒤 `uses`, `feeds`, `integrates-with`, `depends-on`, `supports`, `covers`, `documents`, `references`, `complements`, `receives-signal-from` 등으로 정밀화한다.
- `references`는 고객·운영·synthesis 페이지가 교육 리소스, 개요 페이지, 참고 허브를 증거/참조 대상으로 연결할 때 사용하며, 제품 구현·데이터 흐름·의존 관계에는 사용하지 않는다.
- 자동 스크립트의 `implemented-by` 제안은 개념/방법론 페이지에 과하게 적용될 수 있으므로, 제품 구현 관계가 명확할 때만 사용한다.
- 정밀화 후에는 `build-ontology-sidecar.py` → `check-ontology-relations.py` → `check-ontology.py` → `wiki-quality-gates.py` 순서로 재생성·검증한다.

### Architecture Hardening (v1.14+)

운영 아키텍처는 단일 지표 출처, 질의용 랭킹 보정, strict CI를 기준으로 유지한다.

- 저장소 규모 지표는 `scripts/wiki-stats.py --write-ops`가 생성하는 `outputs/wiki-ops/repo-metrics.json`을 canonical source로 사용한다.
- `wiki-ops-dashboard.py`는 실행 시 repo metrics를 먼저 재생성하고, dashboard JSON/Markdown에 핵심 규모 지표를 포함한다.
- `compute-pagerank.py`는 Raw PageRank와 Query-adjusted rank를 함께 산출한다. 일반 질의 후보 선정은 query-adjusted rank를 우선하고, 원본 PageRank는 구조적 허브 진단용으로 보존한다.
- ontology sidecar는 `[[A]] [relation] [[B]]`로 시작하는 실제 relation 라인만 집계해 후보 표·예시 문장이 지표를 오염시키지 않도록 한다.
- CI는 orphan, ontology, tag drift 실패를 soft warning으로 넘기지 않고 실패로 처리한다.

### Operational Automation (v1.15+)

v1.15부터 운영 정책을 실제 실행 가능한 CLI와 CI guard로 닫는다.

- `wiki-query.py`는 본문·태그·category boost·ontology weight·query-adjusted PageRank를 결합해 질의별 후보 페이지를 산출한다.
- `check-graph-hygiene.py`는 placeholder, unknown target, trailing backslash 등 graph node 오염 원인을 차단하고, table 안의 escaped alias(`\|`)는 정상 alias로 정규화한다.
- `update-metrics-snippets.py`는 README/AGENTS의 metrics block을 `repo-metrics.json`, relation quality, graph output 기준으로 갱신한다.
- `check-related-to-budget.py`는 weak `related-to` 예산을 기본 10개로 제한해 relation drift를 CI에서 차단한다.
- `graph-delta-report.py`는 최신 태그 대비 node/edge/degree 변화를 `outputs/wiki-ops/graph-delta.md`로 기록한다.
- `registry-promotion-workbench.py`는 registry 승격 후보를 review packet으로 압축해 샘플링/보류/승격 판단을 빠르게 한다.
- `release-wiki.py`는 검증, metrics snippet update, commit, tag, push, GitHub Release 생성을 한 번의 CLI로 묶는다.

### Temporal Provenance (v1.16+)

Graphiti의 temporal context graph 설계를 Markdown-native 운영에 맞게 흡수한다. 외부 graph DB를 필수로 두지 않고, 기존 `outputs/wiki-ops/` sidecar 파일로 provenance와 시간성을 추적한다.

- `build-ontology-sidecar.py`는 각 relation에 `relation_id`, `episode_id`, `valid_at`, `invalid_at`, `stale_after`, `fact_status`, `raw_sources`를 기록한다.
- `build-episode-ledger.py`는 wiki 페이지에서 참조된 raw source를 stable `episode_id`로 기록하고, source fingerprint, derived wiki pages, derived ontology relations를 JSONL로 남긴다.
- `wiki-ops-dashboard.py`는 episode count, missing raw reference, ontology-linked episode 수를 함께 표시한다.
- Graphiti MCP/Neo4j/FalkorDB 도입은 선택 사항이다. 기본 템플릿은 로컬 Markdown + JSONL sidecar만으로 동작한다.

### 스케일 전환 기준
- 위키 페이지가 **500+** 이상으로 성장하면 index.md만으로 탐색이 비효율적일 수 있다
- 이 시점에서 **qmd**(로컬 마크다운 검색 엔진, BM25+벡터 하이브리드)를 CLI/MCP 도구로 도입한다
- 참고: [[qmd]] 엔티티 페이지

### Obsidian 도구
- **Web Clipper**: 브라우저 기사 → 마크다운 변환 (수집 경로: `raw/obsidian/Clippings/YYYYMM/` — 자동 월별 정리는 `scripts/organize-collection-by-month.ps1` 사용)
- **Graph View**: 위키 구조 시각화, 허브/고아 페이지 식별 (Lint 시 활용)
- **Dataview 플러그인**: YAML 프론트매터 기반 동적 테이블/리스트 생성
- **이미지 로컬 다운로드**: 설정 → Files and links → Attachment folder path를 `raw/obsidian/outputs/YYYYMM/attachments/` 또는 `raw/obsidian/Clippings/YYYYMM/`로 지정

### 버전 관리
- 위키는 마크다운 파일의 git 레포지토리로 운영할 수 있다
- 버전 히스토리, 브랜칭, 롤백을 무료로 확보한다

### Owen-WIKI 템플릿 킷 (`Owen-WIKI/`)
- 이 WIKI 저장소의 구조·규칙·워크플로우를 패키징한 **재사용 가능한 템플릿 킷**
- 다른 사용자가 동일한 수준의 LLM Wiki를 구축할 수 있도록 AGENTS.md, 스타터 파일, 페이지 템플릿, 온톨로지 템플릿, 바이너리 추출 스크립트를 포함한다
- **버전업 규칙**: WIKI의 다음 항목이 변경되면 Owen-WIKI 킷도 함께 업데이트한다:
  1. AGENTS.md의 워크플로우가 변경될 때
  2. 새로운 레이어/폴더가 추가될 때
  3. 온톨로지 관계코드가 확장될 때
  4. 페이지 타입이 추가될 때
  5. 스크립트가 업데이트될 때
- 변경 이력: `outputs/Owen-WIKI/CHANGELOG.md` (워크스페이스 사본) · `/Users/owen/github/owen-wiki/CHANGELOG.md` (외부 git 저장소)
- 현재 버전: **v1.16.0** (2026-05-22) — Temporal Provenance (Graphiti식 ontology sidecar + episode ledger) 반영
- 경로 동기화**: 템플릿 변경 시 외부 `D:\JAELE\owen-wiki\` (Win) / `/Users/owen/github/owen-wiki/` (macOS) 갱신한다
