# Owen-WIKI 설정 가이드

> 이 가이드를 따라하면 Owen의 LLM Wiki + Knowledge Graph 시스템과 동일한 구조의 개인 위키를 구축할 수 있다.
> 소요 시간: 최초 설정 ~10분, 첫 번째 인제스트 ~10분

---

## Phase 1: 환경 준비

### 1.1 필수 요건

| 항목 | 최소 요건 | 권장 |
|------|----------|------|
| LLM 에이전트 | Claude / GPT / Copilot 등 파일 읽기·쓰기 가능한 에이전트 | VS Code + GitHub Copilot Agent |
| 마크다운 뷰어 | 아무 텍스트 에디터 | Obsidian (Graph View, Dataview, Web Clipper) |
| Python | 3.10+ (바이너리 추출 시) | 3.12 |
| Git | 선택 | 권장 (버전 관리) |

### 1.2 Obsidian 설정 (권장)

1. Obsidian 설치 → 프로젝트 폴더를 Vault로 열기
2. **Settings → Files and links**:
   - Default location for new attachments: `raw/assets/`
   - New link format: `Shortest path when possible`
   - Use `[[Wikilinks]]`: ON
3. **커뮤니티 플러그인 설치**:
   - Dataview: YAML 프론트매터 동적 쿼리
   - Marp Slides: 마크다운 슬라이드 생성
   - Web Clipper (브라우저 확장): 기사 → 마크다운 클리핑

---

## Phase 2: 디렉토리 구조 생성

```bash
# 프로젝트 루트에서 실행
PROJECT_ROOT="my-wiki"  # ← 원하는 이름으로 변경

mkdir -p "$PROJECT_ROOT"/{raw/{assets,articles,papers,notes,extracted},wiki/{entities,concepts,summaries,comparisons,synthesis,ontology},outputs/{presentations,reports,workshops,drafts},scripts,templates}

cd "$PROJECT_ROOT"
```

### 생성되는 구조

```
my-wiki/
├── raw/                   ← 사용자가 소스를 넣는 곳
│   ├── assets/            ← 이미지, CSV 등
│   ├── articles/          ← 웹 기사
│   ├── papers/            ← 논문
│   ├── notes/             ← 메모
│   └── extracted/         ← 바이너리→마크다운 변환 결과
├── wiki/                  ← LLM이 관리하는 위키
│   ├── entities/
│   ├── concepts/
│   ├── summaries/
│   ├── comparisons/
│   ├── synthesis/
│   └── ontology/          ← 관계 그래프
├── outputs/               ← 최종 산출물
├── scripts/
└── templates/
```

---

## Phase 3: 파일 배치

Owen-WIKI 킷에서 파일을 복사한다:

```bash
# 스키마 (가장 중요!)
cp <kit-path>/AGENTS.md ./AGENTS.md

# 초기 파일
cp <kit-path>/starter-files/index.md ./index.md
cp <kit-path>/starter-files/log.md ./log.md

# 온톨로지 초기 파일
cp <kit-path>/ontology-templates/*.md ./wiki/ontology/

# 페이지 템플릿
cp <kit-path>/templates/*.md ./templates/

# 스크립트 (추출 + 린트 유틸리티)
cp <kit-path>/scripts/*.py ./scripts/
```

---

## Phase 4: AGENTS.md 커스터마이징

**반드시 수정해야 할 항목**:

1. `{{PROJECT_ROOT}}` → 실제 프로젝트 경로 (예: `/Users/alice/Research/my-wiki`)
2. `{{YOUR_NAME}}` → 자신의 이름

**도메인에 맞게 조정할 항목**:

- `raw/` 하위 폴더: 자신의 소스 유형에 맞게 추가/제거
  - 예: 개발자 위키라면 `raw/repos/`, `raw/stack-overflow/`
  - 예: 독서 위키라면 `raw/books/`, `raw/highlights/`
- 관계코드: 도메인 고유 관계 추가
  - 예: 의학 → `[treats]`, `[causes]`, `[diagnoses]`
  - 예: 소프트웨어 → `[imports]`, `[calls]`, `[inherits]`
- 페이지 타입: 필요 시 추가
  - `question`: 열린 연구 질문
  - `timeline`: 시간순 정리
  - `data`: 정량 데이터 추적

---

## Phase 5: Git 초기화 (권장)

```bash
git init

cat > .gitignore << 'EOF'
.venv/
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.DS_Store
raw/extracted/
*.bak
EOF

git add -A
git commit -m "init: Owen-WIKI template setup"
```

---

## Phase 6: 첫 번째 인제스트 (테스트)

### 6.1 소스 준비

가장 쉬운 방법: 관심 있는 웹 기사를 마크다운으로 저장한다.

```bash
# 방법 A: Obsidian Web Clipper로 기사 클리핑 → raw/articles/에 저장
# 방법 B: 직접 마크다운 파일 생성
echo "# My First Source\n\nThis is a test article about..." > raw/articles/first-article.md
```

### 6.2 LLM에게 인제스트 지시

VS Code / Cursor에서 LLM 에이전트에게:

```
raw/articles/first-article.md 를 인제스트해줘
```

LLM이 수행할 작업:
1. 소스를 읽고 요약 → `wiki/summaries/first-article.md`
2. 관련 엔티티/개념 페이지 생성
3. `ontology/` 파일에 관계 추가
4. `index.md` 업데이트
5. `log.md` 기록

### 6.3 결과 확인

```bash
# 생성된 파일 확인
ls wiki/summaries/
ls wiki/entities/
cat index.md
cat log.md
```

Obsidian에서 Graph View를 열면 첫 번째 페이지 네트워크가 보인다.

---

## Phase 7: 성장 패턴

### 소스 10개 미만 (시작기)
- 인제스트에 집중
- 온톨로지는 자동으로 축적됨
- 아직 갭 분석은 불필요

### 소스 10~50개 (성장기)
- 첫 번째 Lint 실행: `위키를 점검해줘`
- overview.md 생성 요청
- 갭 분석 결과 확인 → 브릿지 콘텐츠 생성

### 소스 50~200개 (성숙기)
- 정기 Lint (주 1회)
- 갭 기반 연구 방향 설정
- Synthesis 페이지로 주제별 종합
- Comparison 페이지 활성화

### 소스 200개 이상 (확장기)
- qmd 등 검색 엔진 도입 고려
- 온톨로지 클러스터가 안정화
- outputs/ 산출물 생산 본격화

---

## 트러블슈팅

### LLM이 AGENTS.md를 안 읽어요
- AGENTS.md가 프로젝트 루트에 있는지 확인
- LLM 에이전트에게 "AGENTS.md를 읽고 위키 스키마를 따라줘"라고 명시

### 온톨로지가 커져서 읽기 무거워요
- `full-wiki-ontology.md`만 집중적으로 관리 (카테고리별 파일은 보조)
- 클러스터 섹션의 주석을 간결하게 유지

### Obsidian Graph View에서 raw/ 파일이 너무 많아요
- Obsidian Settings → Files and links → Excluded files 에 `raw/` 추가
- 또는 raw/ 를 별도 Vault로 분리

---

## 다음 단계

1. **`SETUP-GUIDE.md`를 완료**했다면 → 소스를 계속 추가하고 인제스트
2. **위키가 10+ 페이지**에 도달하면 → `위키를 린트해줘`
3. **특정 질문**이 있으면 → `{{질문}}에 대해 위키에서 답변해줘`
4. **프레젠테이션**이 필요하면 → `{{주제}}로 Marp 슬라이드 만들어줘`
5. **갭을 메우고 싶으면** → `ontology/gap-analysis.md를 확인하고 P0 갭을 해결해줘`
