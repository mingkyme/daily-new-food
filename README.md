# 오늘의 신상 식품

편의점과 식품업계의 신상품 소식을 날짜별 Markdown으로 발행하는 Astro 정적 사이트입니다.

## 로컬 실행

```bash
npm install
npm run dev
```

## 새 글 추가

`src/content/news/YYYY-MM-DD-slug.md` 파일을 추가합니다.

```markdown
---
title: "2026년 9월 15일 신상 식품 소식"
description: "오늘 확인한 편의점과 식품업계의 신제품"
publishedAt: 2026-09-15
category: "신상 식품"
tags: [CU, GS25, 세븐일레븐, 이마트24]
draft: false
---

## 편의점 신상품

본문과 공식 출처를 작성합니다.
```

홈의 대표 상품은 본문 순서대로 최대 3개를 표시합니다. `### 브랜드 — 상품명 (출시일)` 또는 `- **브랜드 — 상품명 (출시일)**` 형식(번호 목록도 지원)을 사용하며, 상품이 하나뿐이면 하나만 표시합니다. 해당 형식이 없으면 글 설명을 표시합니다.

출처 링크는 목적지를 구분해 표기합니다. 언론 기사는 `출처: 언론 기사 · [기사 보기](URL)`, 확인된 공식 보도자료는 `출처: 공식 보도자료 · [보도자료 보기](URL)`, 브랜드 전체 메뉴는 `참고: 공식 메뉴 · [공식 메뉴 보기](URL)`로 적습니다. 전체 메뉴는 개별 출시 근거가 아니므로 그 한계를 함께 밝힙니다.

## 검증

```bash
node --experimental-strip-types --test src/lib/briefings.test.mjs
npm run astro -- check
npm run build
```

## 배포

`main` 브랜치에 푸시하면 `.github/workflows/deploy.yml`이 GitHub Pages로 자동 배포합니다.

GitHub 저장소의 **Settings → Pages → Source**는 **GitHub Actions**를 사용합니다.

공개 URL: `https://food.mingky.me/`

커스텀 도메인은 `public/CNAME`과 GitHub Pages 설정 양쪽에 `food.mingky.me`로 지정합니다.
