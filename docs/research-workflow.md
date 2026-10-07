# 신상 식품 조사·완료 검사

## 조사 범위와 브라우저

**ego-browser만 사용한다.** 설치된 `ego-browser` 스킬을 먼저 읽고 사용자 목표당 TaskSpace 하나를 만들며, 이후 라운드는 같은 ID와 페이지를 재사용한다. Browser Use·별도 Playwright 브라우저로 우회하지 않는다. 후보 발견, 목록 확인, 기사 원문 검증은 서로 다른 단계다.

1. CU, GS25, 세븐일레븐, 이마트24를 **각각 독립 질의**한다. `CU 출시`, `CU 신상품`처럼 별칭·동사를 바꿔 보완하되 여러 브랜드를 묶지 않는다.
2. `scripts/research_gate.py`의 12개 CATEGORIES도 각각 검색한다. **16개 검색 기록은 예외 없이 필수**다.
3. Google 최근 3일 `after:YYYY-MM-DD before:YYYY-MM-DD`(끝 날짜 다음 날), 네이버 뉴스 기간 설정·최신순을 활용한다. 검색 노출 날짜가 아니라 **원문 발행일**이 최종 기준이다.
4. 아래 공식 출처 4개와 식품음료신문 새상품, 식품저널 신상품, 전자신문 유통·생활 최신 목록을 실제로 연다. **7개 출처 시도 기록은 예외 없이 필수**다. 전문 매체 3곳은 정상 최신 목록 검증이 반드시 필요하며 대체 모드를 허용하지 않는다.
5. 원문별 상품명·브랜드·발행일·실제 목적지 URL과 검증 증거를 저장한다. 구매처·출시일은 별도로 기록하고 모르면 추정하지 않는다. 같은 제품은 출시 이벤트 하나로 합치고 할인만 있는 행사는 제외한다.

### 전문 매체의 실제 신상품 메뉴

- 식품음료신문 새상품: `https://www.thinkfood.co.kr/news/articleList.html?sc_section_code=S1N8&view_type=sm` (`S1N1`은 이슈포커스이며 새상품 목록이 아니다).
- 식품저널 신상품: `https://www.foodnews.co.kr/news/articleList.html?sc_sub_section_code=S2N6&view_type=sm`.
- 전자신문은 실제 유통·생활 최신 목록을 확인한다.

### 공식 출처 시작점과 복구

| 출처 | 시작 URL | 실패 시 복구 |
| --- | --- | --- |
| BGF리테일 / CU | `https://bgfretail.com/press/` | `https://bgfretail.com/`에서 실제 메뉴 확인 |
| GS리테일 / GS25 | `https://www.gsretail.com/news/press-releases` | `https://www.gsretail.com/`에서 실제 메뉴 확인 |
| 이마트24 | `https://www.shinsegaegroupnewsroom.com/category/press/` | 그룹 홈페이지/메뉴 및 이마트24 공식 홈페이지에서 실제 메뉴 확인 |
| 세븐일레븐 | 공식 홈페이지의 실제 메뉴에서 발견한 URL | 홈페이지로 돌아가 뉴스·보도자료 메뉴 재탐색 |

시작 URL은 접근 성공 보장이 아니다. 오류가 나면 실제 홈페이지/메뉴에서 복구하며 `/press`, `/newsroom` 등의 경로를 추측해 성공한 것으로 표시하지 않는다. 세븐일레븐은 알려진 뉴스룸 주소가 있다고 주장하지 않는다. 열지 않은 주소는 `attempts`에 넣지 않는다.

## 추출 실패와 빈 검색

- 전체 링크 앞 N개를 자르는 고정 슬라이스는 금지한다. 메뉴·로그인 링크가 아니라 기사 제목과 연결된 링크를 추출한다.
- Google h3/a 등 하나의 선택자에만 의존하지 않는다. 리디렉션은 실제로 열어 목적지 URL을 기록한다.
- `result_count == 0`은 우선 **추출 오류**다. 페이지 전체 텍스트/접근성 트리/스크린샷을 확인하고 선택자를 복구하거나 다른 질의·엔진에서 재탐색한다.
- `empty_verified`는 서로 다른 실제 URL 두 개 이상에서 명시적 '검색결과 없음'을 확인한 경우에만 사용한다. 각 시도에 `explicit_no_results: true`와 증거가 필요하다. 캡차·접근 거부·로딩·DOM 불일치는 빈 검색이 아니다.
- 404·오류·접근 거부 페이지를 `verified` 최신 목록으로 표시하지 않는다. `article_links`가 없거나 메뉴뿐인 목록도 검증 실패다. 각 링크에 **기사 제목, URL, 기사 상세 확인 여부**를 기록한다.

## 조사 증거와 coverage.json

실행마다 새 디렉터리 `${HERMES_HOME:-$HOME/.hermes}/cron/state/food-research/YYYY-MM-DD/실행ID/`에 ego에서 읽은 텍스트와 추출 결과를 배치별로 저장한다. 과거 증거를 복사하거나 빈 파일·작성한 요약을 실제 페이지 증거로 꾸미지 않는다. 증거는 공개 사이트에 넣지 않는다.

아래는 **스키마 설명용 예시**이며 실제 조사 증거가 아니다. 필수 검색 16개와 출처 7개를 모두 채워야 한다.

```json
{
  "date": "2026-10-07",
  "searches": [{
    "key": "CU", "query": "CU 출시 after:2026-10-04 before:2026-10-08",
    "status": "verified",
    "attempts": [{"url": "실제로 연 검색 URL", "result_count": 8, "evidence_file": "/실제/검색.txt"}]
  }],
  "sources": [{
    "key": "전자신문", "mode": "latest_index", "status": "verified",
    "attempts": [{"url": "실제로 연 최신 목록 URL", "result_count": 10, "evidence_file": "/실제/목록.txt"}],
    "article_links": [{"title": "실제 기사 제목", "url": "실제 기사 상세 URL", "article_detail_observed": true}]
  }],
  "articles": [{
    "brand": "CU", "product": "실제 상품명", "url": "실제 원문 URL",
    "published_date": "2026-10-06", "status": "verified", "source_type": "official",
    "verification_evidence_file": "/실제/기사.json", "date_inferred": false
  }]
}
```

`articles`는 **1개 이상 필수**다. 모든 항목에 브랜드·상품명·원문 URL·`published_date`(ISO 날짜)·검증 증거 파일이 필요하다. `status: verified`, `source_type: official` 또는 `reputable_news`를 사용한다. Google 도메인·네이버 검색 URL은 원문이 아니다. 발행일은 실행일 포함 최근 3개 달력일(당일·전날·전전날)만 허용하며 추론 날짜는 금지한다. 저장 증거에 상품명과 해당 ISO 발행일이 들어 있어야 한다. ego로 실제 관찰한 상품명·발행일과 원문 텍스트를 담은 JSON 텍스트도 허용한다. ISO 변환은 관찰한 날짜의 표기 변환일 뿐, 날짜를 새로 추정하는 것이 아니다. 검증 도구는 출처 평판이나 증거 진실성을 자동 증명하지 못하므로 사람이 원문과 신뢰성을 확인해야 한다.

### 공식 목록 실패의 명시적 대안

공식 4곳만 다음 제한적 대안을 허용한다. 원래 출처 행을 삭제하거나 성공으로 바꾸지 않는다.

```json
{
  "key": "BGF리테일", "status": "failed", "mode": "alternative_source",
  "error_reason": "실제로 관찰한 오류 및 복구 실패 이유",
  "attempts": [
    {"url": "실제로 연 최초 URL", "purpose": "initial", "evidence_file": "/실제/최초.txt"},
    {"url": "실제로 연 다른 홈페이지/메뉴 복구 URL", "purpose": "homepage_menu_recovery", "evidence_file": "/실제/복구.txt"}
  ],
  "article_urls": ["articles에서 개별 검증된 해당 브랜드 원문 URL"]
}
```

- 최초·홈페이지/메뉴 복구를 포함한 **서로 다른 실제 URL 두 개 이상**, 각 저장 증거, 오류 이유가 필수다. 실패 페이지의 `result_count`는 성공 조건이 아니다.
- `alternative_source`는 `article_urls`에 참조된 모든 원문이 `articles`의 해당 브랜드(CU/GS25/세븐일레븐/이마트24) 개별 검증 항목일 때만 허용한다. 신뢰할 수 있는 언론 또는 공식 원문이어야 한다. 다른 브랜드 기사나 미검증 후보를 대신 넣을 수 없다.
- 해당 브랜드에 신상 후보가 없는 경우에만 `mode: empty_search`, `article_urls: []`를 사용할 수 있다. 같은 실패·복구 기록과 해당 브랜드의 **독립적으로 검증된 `empty_verified` 검색**이 필요하다. 이것은 브랜드 검색에서 찾지 못했다는 의미이지 전체 신상 없음의 증명이 아니다.
- 두 모드 모두 반환 `warnings`에 공식 목록 접근 실패와 불완전 조사임을 표시한다. 검사 성공(`ok: true`)은 제한된 대안 증거로 발행 게이트를 통과했다는 뜻이지 공식 출처 전체 확인 완료가 아니다. 보고·본문에 미확인 범위와 경고를 유지한다.
- 전문 매체 3곳에는 이 대안을 적용하지 않는다. 전체 `articles`가 비어 있으면 빈 검색이 있어도 자동 발행하지 않는다.

## 발행 전 검사

```bash
python3 scripts/research_gate.py /절대경로/coverage.json --date YYYY-MM-DD
```

`validate(data)` 인터페이스와 CLI 종료 코드(성공 0, 실패 1)는 유지된다. 결과는 `ok`, `errors`, `warnings`다. 발행·빌드·커밋 전에 검사한다. 누락·추출 실패·원문 증거 부재 시 보완하여 재검사한다. 해결하지 못하면 **정상 완료·신상 없음으로 발행하지 말고** 누락 범위와 이유를 Discord에 보고하며 상태 파일은 갱신하지 않는다. 성공해도 경고가 있으면 숨기지 않는다. 이후 빌드/푸시가 성공한 이벤트만 중복 기록에 추가한다.

## 회귀 확인

```bash
python3 -m unittest discover -s scripts -p 'test_*.py' -v
```

16개 독립 검색, 7개 출처 기록, 3개 정상 전문 매체 목록, 원문 검증, 공식 실패 복구·대안 참조, 독립 빈 검색, 오류·메뉴 거부를 확인한다. 테스트용 합성 데이터는 조사 증거로 사용하지 않는다.
