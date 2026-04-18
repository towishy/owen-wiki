# Full Wiki Ontology — 카테고리 간 통합 관계 그래프
# 위키 전체의 카테고리 횡단 관계를 기록한다
# 각 카테고리별 상세 관계는 개별 ontology 파일 참조
# 형식: [[Source]] [relation] [[Target]]
# 최종 갱신: {{date}}

---

## Cluster Map (클러스터 구성)

# 위키가 성장하면 LLM이 여기에 클러스터를 정의한다.
# 예시:
# ### Cluster A: {{주제1}}
# # Nodes: page-a, page-b, page-c
# # Hub: page-a (가장 높은 연결도)
# # 내부 관계: N

---

## Cross-Cluster Relations (카테고리 횡단 관계)

# 위키가 성장하면 LLM이 여기에 클러스터 간 관계를 기록한다.
# 예시:
# ### A (주제1) ↔ B (주제2)
# [[page-a]] [related-to] [[page-x]]
# # 연결 강도: 강 (3+ 관계)
