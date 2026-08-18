import requests

from rg_fetch import build_candidate_urls, parse_fihrist, request_with_log


def test_build_candidate_urls():
    assert build_candidate_urls('2026-08-18') == [
        'https://www.resmigazete.gov.tr/18.08.2026',
        'https://www.resmigazete.gov.tr/eskiler/2026/08/20260818.htm',
    ]


def test_parse_fihrist_extracts_only_unique_same_day_main_gazette_links():
    html = '''
    <div class="fihrist-item mb-1"><a href="/eskiler/2026/08/20260818-1.htm">Kanun</a></div>
    <div class="fihrist-item mb-1"><a href="/eskiler/2026/08/20260818-2.pdf">Karar</a></div>
    <div class="fihrist-item mb-1"><a href="/eskiler/2026/08/20260818-1.htm">Tekrar</a></div>
    <div class="fihrist-item mb-1"><a href="/eskiler/2026/08/20260817-1.htm">Dün</a></div>
    <div class="fihrist-item mb-1"><a href="/ilanlar/eskiilanlar/2026/08/20260818-3.htm">İlan</a></div>
    '''
    items = parse_fihrist(html, '2026-08-18')
    assert [item['url'] for item in items] == [
        'https://www.resmigazete.gov.tr/eskiler/2026/08/20260818-1.htm',
        'https://www.resmigazete.gov.tr/eskiler/2026/08/20260818-2.pdf',
    ]


class FakeResponse:
    ok = True
    status_code = 200
    url = 'https://www.resmigazete.gov.tr/18.08.2026'
    headers = {'content-type': 'text/html'}
    content = b'<html>ok</html>'


class FakeSession:
    def __init__(self):
        self.verify_values = []

    def get(self, url, timeout, allow_redirects, verify):
        self.verify_values.append(verify)
        if verify:
            raise requests.exceptions.SSLError('certificate verify failed')
        return FakeResponse()


def test_request_retries_without_tls_verification_only_after_ssl_error():
    session = FakeSession()
    response, log = request_with_log(session, 'https://www.resmigazete.gov.tr/18.08.2026')
    assert response is not None
    assert session.verify_values == [True, False]
    assert log['success'] is True
    assert log['tls_verification'] is False
    assert log['fallback_reason'] == 'ssl_certificate_verification_failed'


def test_request_can_reuse_known_tls_workaround_without_retrying_verified_tls():
    session = FakeSession()
    response, log = request_with_log(
        session,
        'https://www.resmigazete.gov.tr/eskiler/2026/08/20260818-1.htm',
        verify_tls=False,
    )
    assert response is not None
    assert session.verify_values == [False]
    assert log['success'] is True
    assert log['tls_verification'] is False
    assert log['fallback_reason'] == 'known_certificate_chain_workaround'
