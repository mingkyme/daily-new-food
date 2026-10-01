import assert from 'node:assert/strict';
import { test } from 'node:test';
import { productHighlights } from './briefings.ts';

test('extracts mixed product formats in order without source or purchase labels', () => {
  assert.deepEqual(productHighlights(`### 1. 브랜드 — 상품 (출시 10월 1일)
- **출처:** [기사](https://example.com)
- **브랜드(한국) — 두 번째 상품 (10월 2일 발표)**
### 기타 안내
3. **브랜드 — 세 번째 상품 (10월 3일 발표)**
### 브랜드 — 네 번째 상품`), ['브랜드 — 상품', '브랜드(한국) — 두 번째 상품', '브랜드 — 세 번째 상품']);
});
test('supports absent products and a single product', () => {
  assert.deepEqual(productHighlights(), []);
  assert.deepEqual(productHighlights('이번 조사에서 추가 신상은 없습니다.'), []);
  assert.deepEqual(productHighlights('- **bhc — 콰삭모짜킹 (9월 24일 출시)**'), ['bhc — 콰삭모짜킹']);
});
