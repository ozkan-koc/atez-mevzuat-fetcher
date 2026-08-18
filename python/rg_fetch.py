from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE = 'https://www.resmigazete.gov.tr'
TIMEOUT = 20

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/151 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8',
    'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
}


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
        if not (filename.startswith(f'{compact}-') and filename.lower().endswith(('.htm', '.pdf'))):
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


def request_with_log(session: requests.Session, url: str) -> tuple[requests.Response | None, dict]:
    started = time.time()
    record = {
        'url': url,
        'started_at': datetime.utcnow().isoformat(timespec='milliseconds') + 'Z',
        'method': 'requests',
    }
    try:
        response = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        record.update({
            'success': response.ok and len(response.content) > 0,
            'status': response.status_code,
            'final_url': response.url,
            'content_type': response.headers.get('content-type', ''),
            'bytes': len(response.content),
            'elapsed_ms': round((time.time() - started) * 1000),
        })
        return response, record
    except Exception as exc:
        record.update({
            'success': False,
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

    for candidate in build_candidate_urls(date):
        response, log = request_with_log(session, candidate)
        logs.append(log)
        print(json.dumps(log, ensure_ascii=False))
        if response is None or not log['success']:
            continue
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
        response, log = request_with_log(session, item['url'])
        logs.append(log)
        print(json.dumps(log, ensure_ascii=False))
        saved = False
        if response is not None and log['success']:
            (raw_dir / item['filename']).write_bytes(response.content)
            saved = True
        documents.append({**item, 'fetched': saved, 'fetch': log})

    manifest = {
        'date': date,
        'selected_source_url': selected_source_url,
        'candidate_urls': build_candidate_urls(date),
        'documents_discovered': len(items),
        'documents_fetched': sum(1 for d in documents if d['fetched']),
        'documents': documents,
        'requests': logs,
    }
    (out_dir / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')

    summary = {
        'date': date,
        'selected_source_url': selected_source_url,
        'documents_discovered': manifest['documents_discovered'],
        'documents_fetched': manifest['documents_fetched'],
        'status': 'PASS' if items and manifest['documents_fetched'] == len(items) else 'BLOCKED',
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary['status'] == 'PASS' else 2


if __name__ == '__main__':
    target_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime('%Y-%m-%d')
    raise SystemExit(run(target_date))
