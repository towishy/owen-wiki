# Entities Ontology
# entities/ 폴더 내 페이지 간 관계 그래프
# 형식: [[Source]] [relation] [[Target]]
# 최종 갱신: {{date}}

# 새 엔티티를 인제스트할 때마다 이 파일 끝에 관계를 추가한다.
# 절대 전체를 재생성하지 않는다 (증분 업데이트 원칙).

## 예시 (첫 인제스트 후 아래와 같이 축적됨)
# [[organization-a]] [contains] [[product-b]]
# [[person-x]] [related-to] [[organization-a]]
# [[customer-y]] [deploys] [[product-b]]
