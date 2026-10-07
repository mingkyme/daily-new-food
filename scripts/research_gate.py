"""Fail closed when required browser research coverage is missing."""
import argparse
import json
from pathlib import Path
from datetime import date
from urllib.parse import urlsplit
import re


def direct_url(value):
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    host = parsed.hostname or ''
    return (parsed.scheme in ('http', 'https') and bool(host)
            and not re.search(r'(^|\.)google\.[a-z.]+$', host)
            and host != 'search.naver.com')


def error_page(text):
    return bool(re.search(r'\b404\b\s*(?:not found)?|\b403\b\s*forbidden|access denied|'
                          r'page not found|페이지를 찾을 수 없습니다|'
                          r'페이지를 표시할 수 없습니다|'
                          r'서비스 이용에 불편을 드려|사이트에 연결할 수 없음|'
                          r'captcha|ERR_[A-Z_]+', text, re.I))


def evidence_text(value):
    try:
        return Path(value).read_text(encoding='utf-8') if isinstance(value, str) else ''
    except (OSError, UnicodeError):
        return ''

BRANDS = ('CU', 'GS25', '세븐일레븐', '이마트24')
CATEGORIES = ('치킨', '카페', '식당·외식', '과자·음료', '베이커리·도넛',
              '디저트·아이스크림', '버거·피자·샌드위치', '밀키트·간편식',
              '면·분식', '유제품·대체식품', '주류', '소스·조미료')
SOURCES = ('BGF리테일', 'GS리테일', '세븐일레븐', '이마트24',
           '식품음료신문', '식품저널', '전자신문')


def validate(data):
    errors = []
    warnings = []
    articles = data.get('articles', [])
    if not isinstance(articles, list) or not articles:
        errors.append('articles: individually verified articles required')
        articles = []
    for index, article in enumerate(articles):
        prefix = f'articles/{index}'
        if not isinstance(article, dict):
            errors.append(f'{prefix}: invalid article')
            continue
        for field in ('brand', 'product', 'url', 'published_date'):
            if not isinstance(article.get(field), str) or not article[field].strip():
                errors.append(f'{prefix}: missing {field}')
        if (article.get('status') != 'verified'
                or article.get('source_type') not in ('official', 'reputable_news')
                or not direct_url(article.get('url')) or article.get('date_inferred')):
            errors.append(f'{prefix}: verified original article required; no inferred date')
        try:
            published = date.fromisoformat(article.get('published_date', ''))
            run_date = date.fromisoformat(data.get('date', ''))
            if not 0 <= (run_date - published).days <= 2:
                raise ValueError('outside recent three calendar days')
        except (ValueError, TypeError):
            errors.append(f'{prefix}: invalid or out-of-window publication date')
        text = evidence_text(article.get('verification_evidence_file'))
        if (not text.strip() or error_page(text) or not article.get('product') or article['product'] not in text
                or not article.get('published_date') or not any(
                    date_token in text for date_token in (
                        article['published_date'], article['published_date'].replace('-', '.')))):
            errors.append(f'{prefix}: saved evidence must contain product and publication date')
    for field, required in (('searches', BRANDS + CATEGORIES), ('sources', SOURCES)):
        rows = {row.get('key'): row for row in data.get(field, []) if isinstance(row, dict)}
        errors.extend(f'{field}: missing {key}' for key in required if key not in rows)
        for key in required:
            if key not in rows:
                continue
            row = rows[key]
            prefix = f'{field}/{key}'
            query = row.get('query', '')
            if field == 'searches' and key in BRANDS:
                if key not in query or any(other in query for other in BRANDS if other != key):
                    errors.append(f'{prefix}: must search this brand independently')
            attempts = row.get('attempts', [])
            if field == 'sources' and row.get('status') == 'failed':
                brand = dict(zip(SOURCES[:4], BRANDS)).get(key)
                refs = row.get('article_urls', [])
                matching = {a.get('url') for a in articles if isinstance(a, dict)
                            and a.get('brand') == brand and a.get('status') == 'verified'
                            and a.get('source_type') in ('official', 'reputable_news')}
                search = next((s for s in data.get('searches', [])
                               if isinstance(s, dict) and s.get('key') == brand), {})
                alternative = (row.get('mode') == 'alternative_source' and bool(refs)
                               and all(url in matching for url in refs))
                empty = (row.get('mode') == 'empty_search'
                         and search.get('status') == 'empty_verified'
                         and not matching and not refs)
                if (not brand or not (alternative or empty)
                        or not row.get('error_reason', '').strip()
                        or len(attempts) < 2
                        or len({a.get('url') for a in attempts}) < 2
                        or attempts[0].get('purpose') != 'initial'
                        or not any(a.get('purpose') == 'homepage_menu_recovery' for a in attempts[1:])):
                    errors.append(f'{prefix}: failed official index requires recovery and verified brand articles')
                for attempt in attempts:
                    if not direct_url(attempt.get('url')) or not evidence_text(attempt.get('evidence_file')).strip():
                        errors.append(f'{prefix}: missing actual recovery URL or saved evidence')
                warnings.append(f'{prefix}: official index unavailable; alternative coverage only, not complete')
                continue
            if row.get('status') not in ('verified', 'empty_verified') or not attempts:
                errors.append(f'{prefix}: unresolved or missing attempts')
                continue
            if field == 'sources':
                links = row.get('article_links', [])
                if not isinstance(links, list) or not links or any(
                        not isinstance(link, dict) or not link.get('title', '').strip()
                        or not direct_url(link.get('url'))
                        or link.get('title', '').strip().lower() in ('menu', '공식 메뉴', '메뉴', '홈', 'home', '뉴스룸', '보도자료')
                        or urlsplit(link.get('url', '')).path.rstrip('/').lower() in ('', '/menu', '/login')
                        or link.get('article_detail_observed') is not True for link in links):
                    errors.append(f'{prefix}: observed article detail links required, not menus')
                if error_page(evidence_text(attempts[-1].get('evidence_file'))):
                    errors.append(f'{prefix}: error page cannot verify an index')
                urls = [str(a.get('url', '')) for a in attempts]
                if row.get('mode') != 'latest_index' or any(not direct_url(u) for u in urls):
                    errors.append(f'{prefix}: direct latest index required, not search results')
            last = attempts[-1]
            count = last.get('result_count', 0)
            if row['status'] == 'empty_verified':
                # A missing DOM selector is not a zero-news day. Require two
                # independent pages with visible explicit no-results messages.
                if field != 'searches' or len(attempts) < 2 or len({a.get('url') for a in attempts}) < 2 or not all(a.get('explicit_no_results') is True for a in attempts):
                    errors.append(f'{prefix}: empty result not independently verified')
            elif not isinstance(count, int) or count < 1:
                errors.append(f'{prefix}: zero extracted results; recover extraction first')
            for attempt in attempts:
                if not str(attempt.get('url', '')).startswith(('https://', 'http://')):
                    errors.append(f'{prefix}: missing browser page URL')
                if not evidence_text(attempt.get('evidence_file')).strip():
                    errors.append(f'{prefix}: missing or empty saved page evidence')
    return {'ok': not errors, 'errors': errors, 'warnings': warnings}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ledger')
    parser.add_argument('--date', required=True)
    args = parser.parse_args()
    try:
        data = json.loads(Path(args.ledger).read_text())
        result = validate(data)
        if data.get('date') != args.date:
            result['errors'].append('Ledger date does not match this run')
        result['ok'] = not result['errors']
    except (OSError, ValueError, TypeError) as error:
        result = {'ok': False, 'errors': [str(error)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['ok'] else 1)
