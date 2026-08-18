from rg_fetch import build_candidate_urls, parse_fihrist


def test_build_candidate_urls():
    assert build_candidate_urls('2026-08-18') == [
        'https://www.resmigazete.gov.tr/18.08.2026',
        'https://www.resmigazete.gov.tr/eskiler/2026/08/20260818.htm',
    ]


def test_parse_fihrist_extracts_unique_same_day_links():
    html = '''
    <div class="fihrist-item mb-1"><a href="/eskiler/2026/08/20260818-1.htm">Kanun</a></div>
    <div class="fihrist-item mb-1"><a href="/eskiler/2026/08/20260818-2.pdf">Karar</a></div>
    <div class="fihrist-item mb-1"><a href="/eskiler/2026/08/20260818-1.htm">Tekrar</a></div>
    <div class="fihrist-item mb-1"><a href="/eskiler/2026/08/20260817-1.htm">Dün</a></div>
    '''
    items = parse_fihrist(html, '2026-08-18')
    assert [item['url'] for item in items] == [
        'https://www.resmigazete.gov.tr/eskiler/2026/08/20260818-1.htm',
        'https://www.resmigazete.gov.tr/eskiler/2026/08/20260818-2.pdf',
    ]
