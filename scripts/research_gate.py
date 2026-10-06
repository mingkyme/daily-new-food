"""Fail closed when required browser research coverage is missing."""
import argparse
import json
from pathlib import Path

BRANDS = ('CU', 'GS25', '세븐일레븐', '이마트24')
CATEGORIES = ('치킨', '카페', '식당·외식', '과자·음료', '베이커리·도넛',
              '디저트·아이스크림', '버거·피자·샌드위치', '밀키트·간편식',
              '면·분식', '유제품·대체식품', '주류', '소스·조미료')
SOURCES = ('BGF리테일', 'GS리테일', '세븐일레븐', '이마트24',
           '식품음료신문', '식품저널', '전자신문')


def validate(data):
    errors = []
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
            if row.get('status') not in ('verified', 'empty_verified') or not attempts:
                errors.append(f'{prefix}: unresolved or missing attempts')
                continue
            if field == 'sources':
                urls = [str(a.get('url', '')) for a in attempts]
                if row.get('mode') != 'latest_index' or any('google.com/' in u or 'search.naver.com/' in u for u in urls):
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
                evidence = Path(attempt.get('evidence_file', ''))
                if not evidence.is_file() or evidence.stat().st_size < 100:
                    errors.append(f'{prefix}: missing or empty saved page evidence')
    return {'ok': not errors, 'errors': errors}


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
