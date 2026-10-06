from pathlib import Path
import tempfile
import unittest
from research_gate import BRANDS, CATEGORIES, SOURCES, validate


class ResearchGateTests(unittest.TestCase):
    def test_incomplete_coverage_is_rejected(self):
        self.assertFalse(validate({'date': '2026-10-06', 'searches': [], 'sources': []})['ok'])

    def test_empty_extraction_and_combined_brand_query_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence = Path(tmp) / 'page.txt'
            evidence.write_text('Test fixture for browser evidence. ' * 10)
            def row(key):
                return {'key': key, 'status': 'verified', 'query': key + ' 출시',
                        'mode': 'latest_index',
                        'attempts': [{'url': 'https://example.org/search', 'result_count': 1,
                                      'evidence_file': str(evidence)}]}
            ledger = {'date': '2026-10-06',
                      'searches': [row(key) for key in BRANDS + CATEGORIES],
                      'sources': [row(key) for key in SOURCES]}
            self.assertTrue(validate(ledger)['ok'])
            ledger['searches'][0]['attempts'][0]['result_count'] = 0
            self.assertFalse(validate(ledger)['ok'], 'Zero extracted results must not pass')
            ledger['searches'][0]['attempts'][0]['result_count'] = 1
            ledger['searches'][0]['query'] = 'CU GS25 세븐일레븐 이마트24 출시'
            self.assertFalse(validate(ledger)['ok'], 'Combined brand queries must not pass')


    def test_search_engine_page_cannot_pass_as_direct_source_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence = Path(tmp) / 'page.txt'
            evidence.write_text('Test fixture for a visible source index. ' * 10)
            def row(key):
                return {'key': key, 'status': 'verified', 'query': key + ' 출시',
                        'mode': 'latest_index',
                        'attempts': [{'url': 'https://example.org/latest', 'result_count': 1,
                                      'evidence_file': str(evidence)}]}
            ledger = {'date': '2026-10-06', 'searches': [row(k) for k in BRANDS + CATEGORIES],
                      'sources': [row(k) for k in SOURCES]}
            ledger['sources'][0]['attempts'][0]['url'] = 'https://www.google.com/search?q=BGF'
            self.assertFalse(validate(ledger)['ok'])


if __name__ == '__main__':
    unittest.main()
