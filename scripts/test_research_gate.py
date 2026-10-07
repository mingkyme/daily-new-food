"""Synthetic fixtures only; never research/publication evidence."""
from pathlib import Path
import copy
import tempfile
import unittest
from research_gate import BRANDS, CATEGORIES, SOURCES, validate


class ResearchGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.evidence = Path(self.tmp.name) / 'page.txt'
        self.evidence.write_text('Synthetic test fixture only. Product Alpha published 2026-10-06. ' * 10)
        def row(key):
            return {'key': key, 'status': 'verified', 'query': key + ' 출시',
                    'mode': 'latest_index', 'attempts': [self.attempt()],
                    'article_links': [{'title': 'Product Alpha launch',
                                       'url': 'https://example.org/news/alpha',
                                       'article_detail_observed': True}]}
        self.ledger = {'date': '2026-10-07',
                       'searches': [row(k) for k in BRANDS + CATEGORIES],
                       'sources': [row(k) for k in SOURCES],
                       'articles': [self.article()]}

    def attempt(self, url='https://example.org/latest'):
        return {'url': url, 'result_count': 1, 'evidence_file': str(self.evidence)}

    def article(self, brand='CU'):
        return {'brand': brand, 'product': 'Product Alpha',
                'url': 'https://example.org/news/alpha', 'published_date': '2026-10-06',
                'source_type': 'reputable_news', 'status': 'verified',
                'verification_evidence_file': str(self.evidence)}

    def test_dotted_publication_date_in_rendered_evidence_is_valid(self):
        self.evidence.write_text('Product Alpha 입력 2026.10.06')
        self.assertTrue(validate(self.ledger)['ok'])

    def test_article_identifier_containing_404_is_not_error_page(self):
        self.evidence.write_text('Product Alpha 2026-10-06 news id=1044042')
        self.assertTrue(validate(self.ledger)['ok'])

    def test_incomplete_coverage_is_rejected(self):
        self.assertFalse(validate({'searches': [], 'sources': []})['ok'])

    def test_empty_extraction_and_combined_brand_query_are_rejected(self):
        self.assertTrue(validate(self.ledger)['ok'])
        self.ledger['searches'][0]['attempts'][0]['result_count'] = 0
        self.assertFalse(validate(self.ledger)['ok'])
        self.ledger['searches'][0]['attempts'][0]['result_count'] = 1
        self.ledger['searches'][0]['query'] = 'CU GS25 세븐일레븐 이마트24 출시'
        self.assertFalse(validate(self.ledger)['ok'])

    def test_search_engine_page_cannot_pass_as_direct_source_index(self):
        self.ledger['sources'][0]['attempts'][0]['url'] = 'https://www.google.com/search?q=BGF'
        self.assertFalse(validate(self.ledger)['ok'])

    def test_indexes_reject_error_pages_and_menu_only_links(self):
        for links in ([], ['https://example.org/menu'],
                      [{'title': 'Menu', 'url': 'https://example.org/menu'}],
                      [{'title': 'Menu', 'url': 'https://example.org/menu',
                        'article_detail_observed': False}]):
            with self.subTest(links=links):
                ledger = copy.deepcopy(self.ledger)
                ledger['sources'][0]['article_links'] = links
                self.assertFalse(validate(ledger)['ok'])
        for text in ('404 Not Found', '페이지를 찾을 수 없습니다', 'Access Denied',
                     '서비스 이용에 불편을 드려 죄송합니다'):
            self.evidence.write_text(text + '\nProduct Alpha 2026-10-06')
            self.assertFalse(validate(self.ledger)['ok'])

    def failed_source(self, key='BGF리테일'):
        return {'key': key, 'status': 'failed', 'mode': 'alternative_source',
                'error_reason': 'Synthetic fixture: index returned an error',
                'attempts': [{**self.attempt('https://example.org/press'), 'purpose': 'initial'},
                             {**self.attempt('https://example.org/'), 'purpose': 'homepage_menu_recovery'}],
                'article_urls': [self.article()['url']]}

    def test_failed_official_source_requires_explicit_article_alternative(self):
        self.ledger['sources'][0] = self.failed_source()
        result = validate(self.ledger)
        self.assertTrue(result['ok'], result)
        self.assertTrue(result['warnings'])
        for field, value in [('error_reason', ''), ('attempts', [self.attempt()]),
                             ('mode', 'latest_index'), ('article_urls', []),
                             ('article_urls', ['https://example.org/not-verified'])]:
            with self.subTest(field=field):
                ledger = copy.deepcopy(self.ledger)
                ledger['sources'][0][field] = value
                self.assertFalse(validate(ledger)['ok'])
        ledger = copy.deepcopy(self.ledger)
        ledger['articles'][0]['brand'] = 'GS25'
        self.assertFalse(validate(ledger)['ok'])
        ledger = copy.deepcopy(self.ledger)
        ledger['sources'][0]['attempts'][1]['url'] = ledger['sources'][0]['attempts'][0]['url']
        self.assertFalse(validate(ledger)['ok'])
        ledger = copy.deepcopy(self.ledger)
        ledger['sources'][4] = self.failed_source('식품음료신문')
        self.assertFalse(validate(ledger)['ok'], 'Food media index has no fallback')

    def test_failed_brand_can_use_independently_empty_search_with_warning(self):
        self.ledger['sources'][0] = {**self.failed_source(),
                                     'mode': 'empty_search', 'article_urls': []}
        self.ledger['articles'][0]['brand'] = 'GS25'
        search = self.ledger['searches'][0]
        search['status'] = 'empty_verified'
        search['attempts'] = [{**self.attempt('https://google.com/search?q=CU'),
                               'explicit_no_results': True},
                              {**self.attempt('https://search.naver.com/search.naver?query=CU'),
                               'explicit_no_results': True}]
        result = validate(self.ledger)
        self.assertTrue(result['ok'], result)
        self.assertTrue(result['warnings'])
        search['attempts'][1]['explicit_no_results'] = False
        self.assertFalse(validate(self.ledger)['ok'])
        search['attempts'][1]['explicit_no_results'] = True
        search['attempts'][1]['url'] = search['attempts'][0]['url']
        self.assertFalse(validate(self.ledger)['ok'])

    def test_verified_labels_do_not_override_error_or_menu_evidence(self):
        for link in ({'title': '공식 메뉴', 'url': 'https://example.org/menu',
                      'article_detail_observed': True},
                     {'title': 'Launch', 'url': 'https://news.google.co.kr/article/1',
                      'article_detail_observed': True}):
            ledger = copy.deepcopy(self.ledger)
            ledger['sources'][0]['article_links'] = [link]
            self.assertFalse(validate(ledger)['ok'])
        self.evidence.write_text('Access Denied Product Alpha 2026-10-06')
        ledger = copy.deepcopy(self.ledger)
        ledger['sources'][0] = self.failed_source()
        self.assertTrue(any(e.startswith('articles/') for e in validate(ledger)['errors']))

    def test_all_sixteen_searches_and_seven_sources_stay_required(self):
        for field in ('searches', 'sources'):
            for index in range(len(self.ledger[field])):
                with self.subTest(field=field, index=index):
                    ledger = copy.deepcopy(self.ledger)
                    ledger[field].pop(index)
                    self.assertFalse(validate(ledger)['ok'])

    def test_gs_error_message_and_regional_google_index_are_rejected(self):
        self.evidence.write_text('페이지를 표시할 수 없습니다. Product Alpha 2026-10-06')
        self.assertFalse(validate(self.ledger)['ok'])
        self.evidence.write_text('Product Alpha 2026-10-06')
        self.ledger['sources'][0]['attempts'][0]['url'] = 'https://www.google.co.kr/search?q=BGF'
        self.assertFalse(validate(self.ledger)['ok'])

    def test_articles_are_required_and_individually_verified(self):
        for change in ({'articles': []}, {'articles': [{}]}):
            with self.subTest(change=change):
                self.assertFalse(validate({**self.ledger, **change})['ok'])
        for field, value in [('brand', ''), ('product', ''), ('published_date', 'yesterday'),
                             ('published_date', '2026-10-01'), ('date_inferred', True),
                             ('url', 'https://news.google.com/articles/abc'),
                             ('status', 'candidate'), ('source_type', 'menu'),
                             ('verification_evidence_file', '/missing')]:
            with self.subTest(field=field, value=value):
                article = {**self.article(), field: value}
                self.assertFalse(validate({**self.ledger, 'articles': [article]})['ok'])
        for content in ('Unrelated saved page. ' * 10,
                        'Product Alpha with no publication date. ' * 10):
            self.evidence.write_text(content)
            self.assertFalse(validate(self.ledger)['ok'])
        self.evidence.write_text('{"product": "Product Alpha", "date": "2026-10-06"}')
        self.assertTrue(validate(self.ledger)['ok'], 'JSON text evidence is valid')


if __name__ == '__main__':
    unittest.main()
