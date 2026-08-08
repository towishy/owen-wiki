---
title: "Owen UI Foundation & Lab 개발 가이드"
type: synthesis
tags: [topic/ui-ux, topic/frontend, topic/design-system, topic/accessibility, topic/testing, type/synthesis]
sources: ["AGENTS.md", "lib/ui-foundation/DESIGN.md", "lib/ui-foundation/AI-USAGE.md", "lib/ui-foundation/README.md", "lib/ui-foundation/src/index.ts", "lib/ui-lab/README.md", "lib/ui-lab/tests/ui-lab.spec.ts"]
created: 2026-08-08
updated: 2026-08-08
confidence: 0.94
last_confirmed: 2026-08-08
stale_after: 2027-02-04
supersedes: []
superseded_by: ""
---

<!-- markdownlint-disable MD025 MD013 MD024 MD028 -->

# Owen UI Foundation & Lab 개발 가이드

## Query Capsule

- **답하는 질문**: Owen 제품 UI를 만들 때 Foundation API와 UI Lab specimen을 어떤 순서와 경계로 선택·조합·검증하는가?
- **핵심 판단/주장**: 화면의 output job을 정의한 뒤 Clear Glass 3종을 가장 먼저 검토하고, 이어서 UI Lab 왼쪽 메뉴의 모든 디자인을 1순위 후보군으로 검토한다. Foundation API와 검증된 composition을 조합하며 앱은 업무 데이터와 copy, orchestration만 소유한다.
- **우선 읽을 섹션**: 1순위 디자인 검토 순서, 60초 의사결정, 화면 라우터, UI Lab 전체 후보 지도, Foundation·앱·Lab 소유권, 구현 절차, 검증 게이트
- **근거 범위**: Owen UI Foundation canonical design/API 문서, package public exports, UI Lab specimen 및 Playwright 회귀 계약
- **보강 확인이 필요한 summary/source**: [[ui-design-system-knowledge]], [[ui-skills-priority-absorption]], [[destructive-confirmation-interaction]], [[emil-kowalski-design-engineering-skills-absorption]]

> [!summary]
> 이 문서는 UI 개발의 실행 라우터다. 시각·동작 결정의 단일 진실 출처는 `lib/ui-foundation/DESIGN.md`, 현재 API와 maturity의 단일 진실 출처는 `lib/ui-foundation/AI-USAGE.md`와 `src/index.ts`다. 이 문서는 그 계약을 제품 화면 설계, 구현, 검증 순서로 연결한다.

> [!decision]
> 기본 순서는 **output job → Clear Glass 3종 → UI Lab 왼쪽 메뉴 전체 → Foundation composition/API → 앱 데이터·copy → 실제 앱 검증**이다. Clear가 1순위 후보군 안에서도 가장 먼저이며, 같은 목적의 Foundation API나 Lab composition이 있으면 앱 전용 디자인을 먼저 만들지 않는다.

> [!important]
> **UI Foundation Lab 왼쪽 패널의 UI 26개는 전부 Priority 1이다.** Clear search, controls, workflow는 그 26개 중 가장 먼저 보는 최우선 3개다. 나머지 23개도 모두 동일한 1순위이며, 앱 전용 신규 디자인이나 외부 reference만 그 다음 순위다.

> [!warning]
> UI Lab의 mockup, sample copy, metric, brand, 전체 화면은 제품 코드로 import하거나 복제하지 않는다. Lab은 독립 transfer specimen과 회귀 검증 표면이다.

## 60초 의사결정

UI 작업을 시작하기 전에 아래 여섯 문장을 채운다.

| 질문 | 기록할 내용 | 좋은 예 |
| --- | --- | --- |
| 누가 쓰는가? | 역할과 사용 맥락 | 보안 분석가가 매일 반복 사용한다 |
| 무엇을 끝내는가? | 한 문장의 output job | evidence 상태를 비교하고 검토 대상을 선택한다 |
| 핵심 데이터는 무엇인가? | 사용자가 판단할 객체 | alert, device, owner, severity, last seen |
| 가장 중요한 명령은 무엇인가? | primary action 1개 | 선택 항목을 검토 큐에 추가한다 |
| 실패하면 무엇을 보여주는가? | 상태와 복구 경로 | partial data를 표시하고 실패 source만 재시도한다 |
| 좁아지면 무엇이 이동하는가? | 책임 단위 reflow | inspector를 본문 아래로 이동한다 |

이 답이 없으면 visual style을 고르지 않는다. 특히 “모던한 대시보드”, “glass UI”, “카드형 화면”은 output job이 아니다.

## 1순위 디자인 검토 순서

Owen UI 개발의 시각 선택은 두 단계로 시작한다. UI Foundation Lab 왼쪽 패널 26개가 모두 1순위이며, 그 안에서 Clear가 가장 먼저다.

### Priority 1A — Clear first

모든 UI 작업에서 다음 specimen을 순서대로 먼저 연다.

| 순서 | Lab specimen | 먼저 판단할 질문 |
| ---: | --- | --- |
| 1 | `#glass-search` · Clear glass search | search, command entry, focal input을 translucent fill·rim·broad shadow로 분리할 수 있는가? |
| 2 | `#glass-controls` · Clear glass controls | segmented mode, filter command, icon dock을 하나의 clear material contract로 묶을 수 있는가? |
| 3 | `#glass-workflow` · Clear glass workflow | form control, menu, primary/secondary action에 같은 재질과 상태 문법을 유지할 수 있는가? |

Clear는 search, toolbar, segmented mode, command, form control, select/menu, overlay, dock, active navigation, widget boundary의 기본 interaction material이다. 적용할 때는 다음 네 요소를 함께 사용한다.

1. Translucent fill
2. Directional rim
3. Backdrop filter
4. Broad low-alpha shadow

blur나 투명 배경 하나만 적용한 것은 Foundation Clear가 아니다. Clear가 1순위라는 말도 긴 본문, dense table, 반복 list row, settings body, data visualization substrate까지 투명하게 만든다는 뜻은 아니다. 이 content body는 opaque surface를 유지하고 그 위의 control·navigation·command layer에 Clear를 적용한다.

### Priority 1B — UI Lab 왼쪽 메뉴 전체

Clear 3종을 검토한 다음에는 UI Lab 왼쪽 navigation에 노출된 모든 specimen을 앱 전용 새 디자인보다 먼저 고려한다. 아래 항목은 모두 1순위 디자인 후보군이다.

| Lab 메뉴 | Lab hash | 우선 검토하는 UI 문제 |
| --- | --- | --- |
| Layered stacks | `#layered-stacks` | preview, persistent label tray, metadata, local command, selected state가 있는 clear layered widget/collection |
| Feature showcase | `#feature-showcase` | 2-6개 기능을 inert UI preview와 짧은 copy로 설명하는 section |
| Micro UI board | `#micro-ui` | compact board, shelf, composer, dock, orb action이 있는 micro collection |
| Theme workbench | `#theme-workbench` | semantic token 편집, scoped preview, contrast validation |
| White instrument | `#instrument-profile` | hero metric 1개, supporting stat, exact progress와 target이 있는 telemetry |
| Glint widgets | `#glint-widgets` | 날씨·일정·배터리처럼 compact contextual signal 1개 |
| Cloud Desk | `#cloud-desk` | stable navigation, opaque work plane, optional utility rail이 있는 quiet workspace |
| Flying panels | `#hierarchical-flying-panels` | stable anchor에서 primary/secondary panel로 깊은 hierarchy 탐색 |
| Food dashboard | `#food-commerce-dashboard` | image-led discovery, compact navigation, persistent order rail |
| Mobile assistant | `#mobile-assistant` | suggestion, collection, composer, bottom dock이 있는 assistant surface |
| Glass frame | `#glass-frame` | back plate와 translucent front pane을 분리한 작은 visual frame |
| Corner ratio | `#corner-ratio` | rounded panel, showcase, identity, pill/circle의 opt-in geometry |
| Settings panels | `#settings-panels` | tone/icon header와 opaque setting row가 있는 설정 section |
| Frosted scrollbar | `#frosted-scrollbar` | native scroll semantics와 local glass grip이 있는 vertical scroll panel |
| Physical book | `#physical-book-interaction` | 소수 이미지 중심 작품·제품 이야기를 고정 순서로 탐색하는 narrative interaction |
| Mobile commerce | `#mobile-commerce` | search, category, product, quantity, primary action, dock이 있는 모바일 구매 흐름 |
| Micro interactions | `#micro-interactions` | copy success, disclosure, occasional overlay, real pending state |
| Motion graphics | `#motion-graphics` | bounded scene orchestration과 React pointer feedback |
| Liquid DOM | `#liquid-dom` | capability-gated renderer와 CSS fallback이 필요한 experimental scene |
| Query builder | `#query-builder` | field/operator/typed-value와 explicit AND/OR가 있는 operational filter |
| Operational data | `#operational-data` | caption, sorting, selection, loading/empty를 갖는 dense table |
| State language | `#state-language` | loading, empty, error, partial, offline, success vocabulary |
| Form and actions | `#form-actions` | field, select, save, ordinary confirmation, high-risk confirmation |

Clear search/controls/workflow도 이 전체 후보군에 포함되지만 항상 가장 먼저 검토하므로 표에서 앞 단계로 분리했다. Lab 메뉴 항목의 API maturity가 experimental 또는 Lab-only여도 “디자인 후보로 먼저 본다”는 순위는 유지한다. 다만 public API import 여부와 production 사용 범위는 maturity 계약을 그대로 따른다.

### 선택 결과 기록

```markdown
Clear review: search / controls / workflow 중 {{adopted_or_rejected}}
Clear placement: {{control, navigation, overlay, dock, active state, widget boundary}}
Opaque body: {{table, text, rows, settings, visualization}}
Lab specimen reviewed: {{left-nav specimen names}}
Selected composition: {{choice}}
Rejected candidates and reason: {{reason}}
```

후보를 검토하지 않고 앱 전용 card, toolbar, navigation, settings panel, data surface를 새로 만드는 것은 Foundation-first가 아니다.

### 구현 brief 템플릿

```markdown
사용자: {{role}}
Output job: {{observable task}}
Primary object: {{data object}}
Primary action: {{single command}}
Composition: {{Foundation/Lab route}}
Required states: loading / empty / error / partial / offline / success
Narrow behavior: {{collapse, move, stack, sheet}}
Validation: keyboard path / axe / overflow / dark / reduced motion / screenshots
```

## 권한과 읽기 순서

충돌 시 아래 순서를 따른다.

1. `AGENTS.md`의 UI Design Foundation-First Workflow
2. `lib/ui-foundation/DESIGN.md`
3. `lib/ui-foundation/AI-USAGE.md`
4. `lib/ui-foundation/README.md`와 `src/index.ts`
5. 관련 `REFERENCE-STUDY-*.md`
6. `lib/ui-lab` specimen과 Playwright test
7. 소비 앱의 기존 화면과 앱 전용 요구

소비 앱의 기존 디자인 시스템이 있다면 Foundation을 통째로 덮어씌우지 않는다. 접근성 primitive와 반복되는 업무 pattern을 우선 재사용하고, 시각 token은 앱의 기존 semantic token과 조정한다.

## Foundation-First 원칙

| 원칙 | 실행 규칙 |
| --- | --- |
| 재사용 우선 | Foundation primitive와 composition을 먼저 조합한다 |
| 소유자 직접 수정 | 공통 결함은 `lib/ui-foundation/src/` 또는 원본 `styles.css` 블록에서 고친다 |
| 앱 책임 유지 | 업무 데이터, 도메인 copy, 권한, API 호출, route orchestration은 앱에 둔다 |
| 증거 기반 확장 | 두 화면 이상에서 반복되고 Lab 검증이 가능한 pattern만 Foundation 후보로 올린다 |
| 상태 완결 | happy path만 구현하지 않고 async·empty·error·partial·offline을 명시한다 |
| 실제 브라우저 검증 | typecheck만으로 UI 완료를 선언하지 않는다 |

## 화면 라우터

먼저 화면 전체의 정보 구조를 고른 뒤 개별 control을 배치한다.

| 화면 목적 | 기본 composition | Foundation API | Lab anchor | 핵심 경계 |
| --- | --- | --- | --- | --- |
| mail, file, review, knowledge, task, operations workspace | Cloud Desk | `WorkbenchShell` family | `#cloud-desk` | stable navigation + opaque work plane + optional rail |
| 깊은 tree를 작업면 위에서 탐색 | Hierarchical Flying Panels | app-owned reference | `#hierarchical-flying-panels` | primary 1개 + secondary 1개, pin 1개만 |
| 반복 widget·collection | Layered Stacks | 앱 조합 | `#layered-stacks` | preview + persistent label tray + local command |
| 기능 2-6개 설명 | Feature Showcase | `FeatureShowcase*` | `#feature-showcase` | inert preview와 copy 분리, 3→2→1열 |
| 설정 화면 | Settings composition | `SettingsPanel*` | `#settings-panels` | tinted header, opaque rows, control reflow |
| 데이터 중심 운영 | Operational composition | `InstrumentPanel`, `OperationalDataTable` | `#instrument-profile`, `#operational-data` | hero metric 1개, data substrate는 opaque |
| field/operator/value 필터 | Query composition | experimental `QueryBuilder` | `#query-builder` | explicit AND/OR, typed value, nested group 제외 |
| 모바일 assistant | Mobile Assistant | `MobileAssistant*` | `#mobile-assistant` | suggestion/list opaque, composer/dock glass |
| 모바일 상품 탐색 | Mobile Commerce | `MobileCommerce*` | `#mobile-commerce` | product/order opaque, primary action 명확 |
| micro collection/library | Micro UI | `MicroUi*` | `#micro-ui` | board/card opaque, command/dock glass |
| compact telemetry | Glint | `GlintWidget` | `#glint-widgets` | widget당 signal 1개 |
| graph workflow builder | app-owned experimental | `@xyflow/react` + 앱 state | source only | `WorkflowBuilder*`를 stable로 가정하지 않음 |
| 이미지 중심 고정 순서 이야기 | Physical Book reference | app-owned state machine | `#physical-book-interaction` | 운영 UI와 긴 reader에는 사용 금지 |

### 화면 라우터 선택 규칙

1. navigation, main, inspector, status가 있으면 `WorkbenchShell`부터 시작한다.
2. 설정은 일반 form/card grid가 아니라 `SettingsPanel` section으로 나눈다.
3. 행과 열을 비교해야 하면 card grid보다 `OperationalDataTable`을 사용한다.
4. 주 수치가 하나가 아니면 여러 `InstrumentPanel`을 만들기 전에 정보 위계를 다시 정한다.
5. 한 화면에 composition을 여러 개 섞을 때는 shell 1개와 content pattern 1-2개로 제한한다.
6. Lab-only reference는 구조를 학습하는 자료이며 package import 대상이 아니다.

## 컴포넌트 라우터

| 요구 | 먼저 사용할 API | 반드시 함께 구현할 계약 | 피할 구현 |
| --- | --- | --- | --- |
| 저장·실행·재시도 | `ActionButton` | loading 중 중복 실행 방지, 명시적 variant | 새 button primitive, clickable `div` |
| label·도움말·오류 입력 | `FormField` | label/help/error/required/disabled ARIA 연결 | label과 error를 따로 조립 |
| option·typeahead 선택 | `SelectControl` | keyboard, form value, popup positioning | 직접 만든 listbox |
| 비동기 영역 | `AsyncState` | loading/empty/error/partial/offline/success | spinner만 표시 |
| compact 상태 | `StatusBadge` | text 또는 icon을 색과 함께 사용 | 색상 dot만 표시 |
| 정렬·선택 표 | `OperationalDataTable` | caption, sort, selection, loading/empty | table을 card grid로 변환 |
| modal·mobile sheet | `ResponsiveOverlay` | Escape, focus restore, narrow sheet | 앱별 focus trap |
| 변경 확인 | `ConfirmableAction` | 결과 copy, async error/success | 모든 확인을 hold로 처리 |
| custom 세로 scroll | `FrostedScrollArea` | native wheel/touch/keyboard 유지 | native semantics 제거 |
| semantic token 편집 | `ThemeWorkbench` | scoped variables, real specimen, contrast | `:root` runtime theme store |
| telemetry panel | `InstrumentPanel` | metric 1개, exact value, target semantics | generic card style |
| 작은 visual frame | `GlassFrameWindow` | back plate/front pane 분리 | 모든 panel에 frame 적용 |

### API maturity

| 등급 | API | 사용 기준 |
| --- | --- | --- |
| Preferred core | `ActionButton`, `FormField`, `SelectControl`, `StatusBadge`, `AsyncState`, `OperationalDataTable`, `WorkbenchShell*`, `ConfirmableAction`, `ResponsiveOverlay` | 새 업무 화면의 기본 선택 |
| Preferred opt-in | `SettingsPanel*`, `ThemeWorkbench`, `InstrumentPanel`, `GlintWidget`, `FrostedScrollArea`, `GlassFrameWindow` | output job이 정확히 맞을 때 |
| Reference composition | `FeatureShowcase*`, `MobileAssistant*`, `MobileCommerce*`, `MicroUi*` | 정보 구조가 맞을 때, 앱 copy/data 유지 |
| Experimental | `QueryBuilder`, `WorkflowBuilder*` | 경계를 문서화하고 앱 검증을 추가할 때만 |
| Internal | package root에서 export되지 않은 module | 우회 import 금지 |

export가 존재하는 것과 stable contract인 것은 다르다. 실제 import 가능 여부는 `lib/ui-foundation/src/index.ts`, maturity는 `AI-USAGE.md`에서 함께 확인한다.

## Foundation·앱·Lab 소유권

| 관심사 | Foundation 소유 | 소비 앱 소유 | UI Lab 소유 |
| --- | --- | --- | --- |
| native semantics·keyboard | 공통 primitive behavior | 화면별 shortcut와 workflow | 회귀 검증 |
| component anatomy | public API와 slot | API 조합 | 독립 specimen |
| visual token | semantic default와 Styles API | 앱 범위 token mapping | light/dark specimen |
| 업무 copy·데이터 | 소유하지 않음 | canonical owner | sample만 사용 |
| loading/error vocabulary | 공통 상태 표현 | 실제 원인·복구 action | 대표 state 검증 |
| responsive behavior | component/container contract | page responsibility 이동 | viewport·container 검증 |
| 접근성 | primitive ARIA와 behavior | 정확한 label·reading order | axe·keyboard evidence |
| 제품 claim·metric | 소유하지 않음 | source와 truth contract | 절대 source가 아님 |

다음 질문 중 하나라도 “예”이면 앱 전용 구현으로 시작한다.

- 특정 도메인의 데이터 schema나 권한에 묶이는가?
- 한 화면에서만 쓰이고 재사용 가능성이 불명확한가?
- 공통 API로 만들면 prop이 업무 용어를 알아야 하는가?
- Lab specimen 없이 responsive·keyboard contract를 설명하기 어려운가?

## Surface와 시각 언어

### Clear Glass 사용

Clear Glass는 기능적 경계에 사용한다.

| 권장 | 불투명 유지 |
| --- | --- |
| search, toolbar, segmented mode | 긴 본문 |
| command, select/menu, overlay | dense table |
| dock, active navigation | 반복 list row |
| widget boundary, contextual panel | settings body |
| 의미 있는 active/selected state | data visualization substrate |

Glass는 translucent fill, directional rim, backdrop filter, broad low-alpha shadow를 한 묶음으로 사용한다. blur만 추가하거나 모든 card를 투명하게 만들지 않는다.

### Geometry와 계층

- 일반 운영 panel은 8px radius를 유지한다.
- control은 6px radius 또는 명시적인 pill/circle 계약을 사용한다.
- rounded-panel ratio는 새로 의도한 rounded surface에만 opt-in한다.
- rounded surface에 vertical left accent rail을 결합하지 않는다.
- page section을 floating card로 감싸지 않고 card 안에 card를 중첩하지 않는다.
- 1px border로 형태를 먼저 정의하고 넓고 낮은 alpha shadow로 elevation을 표현한다.
- stable dimension, grid track, aspect ratio로 hover·loading·label 변화에 따른 layout shift를 막는다.

### Typography와 icon

- Aptos 또는 Pretendard Variable, Segoe UI Variable 순의 Foundation stack을 따른다.
- letter spacing은 0이다.
- 업무 panel heading은 compact하게 유지하고 hero scale은 실제 focal metric 하나에만 쓴다.
- metric과 numeric column에는 tabular numerals를 사용한다.
- familiar tool action은 Lucide icon을 우선하고 icon-only button에는 accessible name을 제공한다.
- 상태는 색만으로 전달하지 않고 text, icon, ARIA state를 함께 사용한다.

### Motion

- pointer press는 140ms `scale(0.97)` 수준을 허용한다.
- keyboard selection과 navigation은 즉시 반영한다.
- overlay와 disclosure 외의 반복 entrance animation을 피한다.
- loading indicator는 실제 pending 상태에만 연결한다.
- reduced motion에서는 positional transform, 반복 motion, 자동 재생을 제거하고 최종 상태를 즉시 보여준다.

## Focus와 접근성

Foundation은 focus rim을 사용하지 않는다. `outline`, focus-only `box-shadow`, focus-only border, parent lift를 만들지 않는다. 대신 background, text, icon, surface 변화처럼 레이아웃과 rim을 만들지 않는 방식으로 keyboard focus를 식별한다.

필수 확인:

1. keyboard만으로 primary workflow를 완료할 수 있다.
2. focus 전후 computed `outline-style`은 `none`이다.
3. focus 전후 `box-shadow`와 border가 focus 때문에 바뀌지 않는다.
4. focusable control을 포함한 parent에도 `:focus-within` rim이나 lift가 없다.
5. dialog는 Escape로 닫히고 trigger로 focus가 돌아간다.
6. icon-only action은 visible tooltip 또는 context와 accessible name을 가진다.
7. 오류는 control과 `aria-describedby`/`aria-invalid`로 연결된다.
8. forced colors와 200% zoom에서도 의미와 조작 경로가 남는다.

`ResponsiveOverlay.trigger`에는 내부 button으로 감싸질 비상호작용 `span`을 전달한다. `ActionButton`처럼 이미 interactive한 element를 넣지 않는다.

## Scroll과 밀도

스크롤 가능한 제품 panel에는 `FrostedScrollArea`를 기본 후보로 사용한다. native wheel, touch, keyboard semantics는 viewport에 남기고 Foundation의 2px rail과 44px local glass grip을 사용한다.

예외:

- horizontal chip/tab scroller
- 운영체제 scrollbar를 명시적으로 존중해야 하는 화면
- virtualized list engine이 scrollbar를 직접 소유하는 화면
- browser document 자체의 page scroll

keyboard로 직접 스크롤해야 하면 `viewportProps={{ tabIndex: 0, "aria-label": "..." }}`를 제공한다. panel content를 단순히 `overflow: hidden`으로 잘라 focusable element를 숨기지 않는다.

## 반응형 설계

반응형은 크기 축소가 아니라 책임 재배치다.

| 넓은 화면 | 좁은 화면 |
| --- | --- |
| sidebar + main + inspector | compact navigation + main + inspector below |
| modal | bottom sheet |
| 3-column feature showcase | 2-column, 이후 1-column |
| settings row의 trailing control | description 아래 control |
| persistent utility rail | work plane 아래 utility section |
| movable/resizable flying panel | in-flow disclosure |

검증 폭은 viewport만 보지 않는다. sidebar, inspector, split pane 안의 실제 component container 폭도 검사한다. 320px viewport에서도 44px target, type hierarchy, radius token을 줄이지 않는다.

## 상태 설계

모든 data surface는 해당되는 상태를 명시적으로 설계한다.

| 상태 | 사용자가 알아야 할 것 | 기본 표현 |
| --- | --- | --- |
| loading | 무엇을 기다리는가 | 구조를 유지한 pending state |
| empty | 데이터가 없는 이유와 다음 행동 | 설명 + 생성/필터 해제 action |
| error | 실패 범위와 복구 방법 | 근처 오류 + retry 또는 설정 이동 |
| partial | 무엇이 성공·실패했는가 | usable data + source별 경고 |
| offline | 로컬에서 가능한 범위 | cached state + reconnect 안내 |
| success | 무엇이 바뀌었는가 | 결과 확인, 필요 시 다음 action |
| disabled | 왜 실행할 수 없는가 | 이유가 보이는 label/help |

spinner는 상태 모델이 아니다. 실패한 source 하나 때문에 usable data 전체를 숨기지 않는다.

## Styles API와 CSS 확장

기본 stylesheet는 app root에서 한 번만 import한다.

```tsx
import "@owen-wiki/ui-foundation/styles.css"

import {
  ActionButton,
  AsyncState,
  FormField,
  SelectControl,
} from "@owen-wiki/ui-foundation"
```

내부 `src/*` 경로를 직접 import하지 않는다. 공개된 Styles API가 있으면 내부 class와 DOM nesting을 추측하지 않는다.

```tsx
import {
  responsiveOverlayStylesApi,
  selectControlStylesApi,
  settingsPanelStylesApi,
} from "@owen-wiki/ui-foundation"
```

### CSS 변경 결정

| 상황 | 수정 위치 |
| --- | --- |
| 모든 소비 앱에서 같은 결함 | Foundation owning component 또는 원본 CSS block |
| 앱의 브랜드·밀도·도메인 차이 | 앱 범위 semantic variable 또는 공개 Styles API |
| 내부 selector를 알아야만 가능한 변경 | Foundation API 부족으로 판단하고 owner API 확장 검토 |
| 한 번만 쓰는 장식 | 앱 component에 유지 |

late override, polish layer, hotfix block을 쌓지 않는다. Foundation owner의 문제라면 원본에서 고치고 충돌하는 후속 보정을 제거한다.

## UI Lab 사용법

UI Lab은 “무엇을 복사할까”가 아니라 “무엇을 검증해야 하나”를 답한다.

### specimen을 보는 순서

1. Clear search, controls, workflow를 먼저 열어 interaction material을 판단한다.
2. 왼쪽 navigation 전체에서 output job과 가까운 specimen을 모두 후보로 검토한다.
3. `AI-USAGE.md`의 Task router에서 선택한 API와 maturity를 확인한다.
4. Lab hash로 이동해 anatomy와 기본 상호작용을 확인한다.
5. desktop과 mobile에서 reflow를 비교한다.
6. keyboard, Escape, focus restore, state announcement를 실행한다.
7. dark theme와 reduced motion을 켠다.
8. 제품 앱에는 실제 data, copy, permission, API state로 다시 조합한다.
9. 실제 앱 URL에 Generic URL Audit을 실행한다.

### 핵심 specimen 지도

| 확인할 문제 | Lab hash | 확인 포인트 |
| --- | --- | --- |
| Clear interaction · 최우선 | `#glass-search`, `#glass-controls`, `#glass-workflow` | translucent fill, directional rim, backdrop filter, broad shadow와 opaque body 경계 |
| Clear layered widget | `#layered-stacks` | preview layer, persistent tray, metadata, local command, selected state |
| 업무 shell | `#cloud-desk` | sidebar/work plane/rail 책임과 container query |
| settings | `#settings-panels` | tone header, opaque row, control reflow |
| form과 action | `#form-actions` | field ARIA, select, press/hold confirmation |
| 비동기 상태 | `#state-language` | loading, empty, offline vocabulary |
| data table | `#operational-data` | caption, sort, selection, loading/empty |
| query builder | `#query-builder` | AND/OR, typed value, narrow reflow |
| telemetry | `#instrument-profile` | exact progress, target, action, dark profile |
| widget | `#glint-widgets` | semantic value와 responsive grid |
| custom scroll | `#frosted-scrollbar` | native scroll와 fixed local grip |
| overlay motion | `#micro-interactions` | pending, disclosure, copy success, overlay |
| feature explanation | `#feature-showcase` | inert preview, external copy, 3→2→1열 |

### Lab에서 가져오지 않는 것

- sample product name과 marketing copy
- sample metric과 test count
- mockup 전체 layout의 무비판적 복제
- Lab source의 private class selector
- experimental renderer를 feature detection 없이 사용
- screenshot을 실제 제품 검증 증거로 재사용

## 구현 절차

### 1. Inventory

- `DESIGN.md`, `AI-USAGE.md`, `README.md`, `src/index.ts`를 읽는다.
- Clear search/controls/workflow를 먼저 검토한다.
- UI Lab 왼쪽 navigation 전체에서 관련 specimen을 고르고 검토·제외 이유를 기록한다.
- 관련 reference study를 고른다.
- 소비 앱의 framework, token, 기존 primitive, global CSS owner를 확인한다.
- `components.json`이 있는 앱에서만 필요 시 `shadcn info --json`을 사용한다.

### 2. Composition

- output job에 맞는 shell/composition을 하나 고른다.
- 실제 content hierarchy를 먼저 배치한다.
- primary action은 하나로 분명하게 만든다.
- page section을 card로 감싸지 않는다.

### 3. Primitive

- button, field, select, state, table, overlay를 Foundation API로 교체한다.
- accessible name과 상태 prop을 실제 업무 의미로 채운다.
- 앱 전용 adapter는 data mapping과 copy에만 집중한다.

### 4. State와 responsive

- loading, empty, error, partial, offline, success 중 필요한 상태를 구현한다.
- narrow viewport와 nested container에서 responsibility를 이동한다.
- scroll owner를 하나로 정하고 필요한 panel에 `FrostedScrollArea`를 적용한다.

### 5. Visual treatment

- opaque content plane을 먼저 확정한다.
- 기능적 control과 경계에만 Clear Glass를 적용한다.
- semantic color, radius, shadow, type token을 사용한다.
- hover, active, selected, disabled, focus를 실제 브라우저에서 확인한다.

### 6. Validation

- 가장 가까운 Foundation/unit check를 실행한다.
- Lab E2E에서 관련 specimen을 검증한다.
- 실제 앱 URL을 320-1440px에서 감사한다.
- 변경 전 운영 화면과 변경 후 로컬 화면을 같은 viewport에서 비교한다.
- focus control의 computed style과 screenshot을 직접 확인한다.

## 검증 게이트

### Foundation과 Lab

```powershell
npm run check --prefix lib/ui-foundation
npm run check --prefix lib/ui-lab
.\.venv\Scripts\python.exe scripts\check-ui-reference-studies.py
```

위 예시의 Python 경로는 저장소 `.venv`가 있을 때 사용한다. 환경에 따라 `python scripts\check-ui-reference-studies.py`로 실행한다.

### 관련 specimen만 빠르게 검증

```powershell
npm run test:e2e --prefix lib/ui-lab -- --grep "settings"
npm run test:e2e --prefix lib/ui-lab -- --grep "query builder"
npm run test:e2e --prefix lib/ui-lab -- --grep "Cloud Desk"
```

### 실제 URL 감사

```powershell
npm run audit:url --prefix lib/ui-lab -- http://127.0.0.1:4173 --output ../../dev/temp/ui-audit
```

감사는 six viewport, axe A/AA, navigation/resource failure, console/page error, broken image, horizontal overflow, reduced-motion infinite animation을 검사한다. warning은 screenshot에서 직접 판정한다.

### 완료 전 체크리스트

- [ ] output job과 primary action이 한 문장으로 설명된다.
- [ ] Clear search, controls, workflow를 가장 먼저 검토했다.
- [ ] UI Lab 왼쪽 navigation에서 output job과 관련된 모든 specimen을 후보로 검토했다.
- [ ] 채택한 Clear layer와 opaque content body의 경계를 기록했다.
- [ ] package root public API만 import했다.
- [ ] API maturity와 Lab anchor를 확인했다.
- [ ] loading/empty/error/partial/offline/success 중 필요한 상태가 있다.
- [ ] 320px viewport와 좁은 nested container에 수평 overflow가 없다.
- [ ] keyboard로 primary workflow를 완료했다.
- [ ] focus에 outline, ring, border 변화, shadow, parent lift가 없다.
- [ ] modal Escape와 trigger focus restore가 동작한다.
- [ ] dense content는 opaque이고 glass가 기능적 경계에 제한된다.
- [ ] scrollable panel은 `FrostedScrollArea` 적용 또는 예외 이유가 있다.
- [ ] dark, reduced motion, forced colors, 200% zoom을 확인했다.
- [ ] axe violation, runtime error, failed resource, broken image가 없다.
- [ ] 변경 전·후를 같은 viewport screenshot으로 비교했다.
- [ ] text overlap, nested card, layout shift, 과도한 glass가 없다.

## 공통 anti-pattern과 교정

| Anti-pattern | 문제 | 교정 |
| --- | --- | --- |
| 모든 section을 card로 감쌈 | hierarchy가 평평해짐 | full-width/in-flow section + 실제 반복 item만 card |
| 모든 표면에 glass | 대비·성능·의미 저하 | control/boundary만 glass, content는 opaque |
| 앱별 button/input 재구현 | semantics와 state drift | `ActionButton`, `FormField`, `SelectControl` |
| spinner만 사용 | empty/error/offline 구분 불가 | `AsyncState` vocabulary 적용 |
| table을 card grid로 표시 | 비교·정렬·scan 저하 | `OperationalDataTable` |
| viewport media query만 사용 | nested pane overflow | container width 기준 reflow 검증 |
| focus ring을 다른 색으로 교체 | 금지된 rim 유지 | background/text/icon 변화로 focus 식별 |
| 내부 class에 override | Foundation 업데이트에 취약 | Styles API 또는 owner API 확장 |
| Lab 화면 그대로 복사 | sample data와 목적이 제품에 섞임 | anatomy/state만 학습해 앱 데이터로 재조합 |
| experimental export를 stable로 사용 | 회귀 계약 부족 | app-owned composition + 명시적 local test |
| hold confirm 남용 | 일상 작업 지연 | routine은 press, 고위험 영구 작업만 hold |
| hover-only command | keyboard/touch 경로 부재 | visible/focus/touch equivalent action 제공 |

## Foundation 승격 기준

앱 전용 pattern을 Foundation으로 올리려면 모두 충족해야 한다.

1. 실제 앱 두 곳 이상에서 같은 문제가 반복된다.
2. domain data와 copy 없이 API를 설명할 수 있다.
3. public prop과 slot이 최소하며 내부 DOM을 숨길 수 있다.
4. keyboard, screen reader, focus restoration 계약이 있다.
5. narrow container, dark, reduced motion, forced colors behavior가 정의된다.
6. 독립 UI Lab specimen과 hash navigation이 있다.
7. unit, axe, keyboard, E2E, visual regression이 있다.
8. `src/index.ts`, `AI-USAGE.md`, `README.md`, 관련 reference study를 함께 갱신한다.

검증이 끝나기 전에는 experimental을 preferred로 올리지 않는다.

## PR 설명 템플릿

```markdown
## UI contract

- Output job: {{task}}
- Foundation composition: {{composition}}
- Foundation APIs: {{components}}
- App-owned behavior: {{data/copy/orchestration}}
- Lab evidence: {{hash/specimen}}

## States and responsive

- States: {{loading/empty/error/partial/offline/success}}
- Narrow behavior: {{reflow}}
- Scroll owner: {{viewport/FrostedScrollArea/exception}}

## Validation

- Foundation/Lab checks: {{result}}
- Keyboard/focus: {{result}}
- Axe/overflow/runtime: {{result}}
- Before/after screenshots: {{paths}}
```

## 관련 페이지

- [[ui-design-system-knowledge]] — Owen UI/디자인 지식 허브와 기본 조합
- [[ui-skills-priority-absorption]] — 외부 UI skill을 보조 점검 관점으로 흡수하는 기준
- [[destructive-confirmation-interaction]] — 고위험 press/hold confirmation 계약
- [[emil-kowalski-design-engineering-skills-absorption]] — 모션·직접 조작·interruptibility 검토
- [[tweakcn-nothing-design-absorption]] — token authoring과 telemetry profile의 선택적 흡수 경계
