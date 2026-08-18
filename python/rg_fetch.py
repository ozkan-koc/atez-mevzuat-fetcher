from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
import urllib3
from bs4 import BeautifulSoup

from supporting_sources import fetch_supporting_sources

BASE = 'https://www.resmigazete.gov.tr'
TIMEOUT = 20

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/151 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8',
    'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
}

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def build_candidate_urls(date: str) -> list[str]:
    dt = datetime.strptime(date, '%Y-%m-%d')
    dotted = dt.strftime('%d.%m.%Y')
    compact = dt.strftime('%Y%m%d')
    return [
        f'{BASE}/{dotted}',
        f'{BASE}/eskiler/{dt:%Y/%m}/{compact}.htm',
    ]


def parse_fihrist(html: str, date: str) -> list[dict]:
    dt = datetime.strptime(date, '%Y-%m-%d')
    compact = dt.strftime('%Y%m%d')
    expected_prefix = f'/eskiler/{dt:%Y/%m}/{compact}-'
    soup = BeautifulSoup(html, 'html.parser')
    candidates = soup.select('div.fihrist-item.mb-1 a[href]')
    if not candidates:
        candidates = soup.select('a[href]')

    seen: set[str] = set()
    items: list[dict] = []
    for anchor in candidates:
        href = anchor.get('href')
        if not href:
            continue
        url = urljoin(BASE, href)
        path = urlparse(url).path
        filename = path.rsplit('/', 1)[-1]
        if not path.startswith(expected_prefix):
            continue
        if not filename.lower().endswith(('.htm', '.pdf')):
            continue
        if url in seen:
            continue
        seen.add(url)
        items.append({
            'title': ' '.join(anchor.get_text(' ', strip=True).split()),
            'url': url,
            'filename': filename,
        })
    return items


def _response_record(response: requests.Response, started: float, verify_tls: bool) -> dict:
    return {
        'success': response.ok and len(response.content) > 0,
        'status': response.status_code,
        'final_url': response.url,
        'content_type': response.headers.get('content-type', ''),
        'bytes': len(response.content),
        'tls_verification': verify_tls,
        'elapsed_ms': round((time.time() - started) * 1000),
    }


def request_with_log(
    session: requests.Session,
    url: str,
    *,
    verify_tls: bool = True,
) -> tuple[requests.Response | None, dict]:
    started = time.time()
    record = {
        'url': url,
        'started_at': datetime.now(UTC).isoformat(timespec='milliseconds'),
        'method': 'requests',
    }

    if not verify_tls:
        try:
            response = session.get(url, timeout=TIMEOUT, allow_redirects=True, verify=False)
            record.update(_response_record(response, started, False))
            record['fallback_reason'] = 'known_certificate_chain_workaround'
            return response, record
        except Exception as exc:
            record.update({
                'success': False,
                'tls_verification': False,
                'fallback_reason': 'known_certificate_chain_workaround',
                'error': f'{type(exc).__name__}: {exc}',
                'elapsed_ms': round((time.time() - started) * 1000),
            })
            return None, record

    try:
        response = session.get(url, timeout=TIMEOUT, allow_redirects=True, verify=True)
        record.update(_response_record(response, started, True))
        return response, record
    except requests.exceptions.SSLError as exc:
        verified_error = f'{type(exc).__name__}: {exc}'
        try:
            response = session.get(url, timeout=TIMEOUT, allow_redirects=True, verify=False)
            record.update(_response_record(response, started, False))
            record.update({
                'fallback_reason': 'ssl_certificate_verification_failed',
                'verified_tls_error': verified_error,
            })
            return response, record
        except Exception as fallback_exc:
            record.update({
                'success': False,
                'tls_verification': False,
                'fallback_reason': 'ssl_certificate_verification_failed',
                'verified_tls_error': verified_error,
                'error': f'{type(fallback_exc).__name__}: {fallback_exc}',
                'elapsed_ms': round((time.time() - started) * 1000),
            })
            return None, record
    except Exception as exc:
        record.update({
            'success': False,
            'tls_verification': True,
            'error': f'{type(exc).__name__}: {exc}',
            'elapsed_ms': round((time.time() - started) * 1000),
        })
        return None, record


def run(date: str) -> int:
    datetime.strptime(date, '%Y-%m-%d')
    out_dir = Path('out') / date
    raw_dir = out_dir / 'raw'
    raw_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update(HEADERS)

    logs: list[dict] = []
    source_response: requests.Response | None = None
    selected_source_url: str | None = None
    items: list[dict] = []
    verify_tls = True

    for candidate in build_candidate_urls(date):
        response, log = request_with_log(session, candidate, verify_tls=verify_tls)
        logs.append(log)
        print(json.dumps(log, ensure_ascii=False), flush=True)
        if response is None or not log['success']:
            continue
        if log.get('tls_verification') is False:
            verify_tls = False
        parsed = parse_fihrist(response.text, date)
        log['fihrist_items_found'] = len(parsed)
        if parsed:
            source_response = response
            selected_source_url = candidate
            items = parsed
            break

    if source_response is not None:
        (raw_dir / 'fihrist.html').write_bytes(source_response.content)

    documents = []
    for item in items:
        response, log = request_with_log(session, item['url'], verify_tls=verify_tls)
        logs.append(log)
        print(json.dumps(log, ensure_ascii=False), flush=True)
        saved = False
        if response is not None and log['success']:
            (raw_dir / item['filename']).write_bytes(response.content)
            saved = True
        documents.append({**item, 'fetched': saved, 'fetch': log})
        time.sleep(0.75)

    supporting = fetch_supporting_sources(date, out_dir, HEADERS)
    print(json.dumps({
        'supporting_sources': {
            'tariff_status': supporting['tariff']['status'],
            'tariff_items': len(supporting['tariff']['items']),
            'resmi_gazete_ozeti_status': supporting['resmi_gazete_ozeti']['status'],
            'resmi_gazete_ozeti_items': len(supporting['resmi_gazete_ozeti']['items']),
        }
    }, ensure_ascii=False), flush=True)

    manifest = {
        'date': date,
        'selected_source_url': selected_source_url,
        'candidate_urls': build_candidate_urls(date),
        'source_policy': {
            'primary_legal_evidence': 'resmigazete.gov.tr',
            'supporting_sources': ['tariff.singlewindow.io', 'resmigazeteozeti.com'],
            'supporting_sources_are_not_legal_evidence': True,
        },
        'tls_policy': {
            'verified_first': True,
            'certificate_chain_workaround_used': not verify_tls,
            'warning': 'verify=False is used only after the host certificate-chain verification failure is observed and logged.',
        },
        'documents_discovered': len(items),
        'documents_fetched': sum(1 for d in documents if d['fetched']),
        'documents': documents,
        'requests': logs,
        'supporting_sources': {
            'tariff_status': supporting['tariff']['status'],
            'tariff_items': len(supporting['tariff']['items']),
            'resmi_gazete_ozeti_status': supporting['resmi_gazete_ozeti']['status'],
            'resmi_gazete_ozeti_items': len(supporting['resmi_gazete_ozeti']['items']),
        },
    }
    (out_dir / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')

    summary = {
        'date': date,
        'selected_source_url': selected_source_url,
        'documents_discovered': manifest['documents_discovered'],
        'documents_fetched': manifest['documents_fetched'],
        'supporting_sources': manifest['supporting_sources'],
        'status': 'PASS' if items and manifest['documents_fetched'] == len(items) else 'BLOCKED',
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return 0 if summary['status'] == 'PASS' else 2


if __name__ == '__main__':
    target_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime('%Y-%m-%d')
    raise SystemExit(run(target_date))
