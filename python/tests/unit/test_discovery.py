from atez_collector.official.discovery import build_candidate_urls, parse_fihrist


def test_build_candidate_urls():
    assert build_candidate_urls("2026-08-18") == [
        "https://www.resmigazete.gov.tr/18.08.2026",
        "https://www.resmigazete.gov.tr/eskiler/2026/08/20260818.htm",
    ]


def test_parse_fihrist_keeps_unique_same_day_official_documents():
    html = """
    <a href="/eskiler/2026/08/20260818-1.htm">Kanun</a>
    <a href="/eskiler/2026/08/20260818-2.pdf">Karar</a>
    <a href="/eskiler/2026/08/20260818-1.htm">Tekrar</a>
    <a href="/eskiler/2026/08/20260817-1.htm">Dün</a>
    <a href="/ilanlar/eskiilanlar/2026/08/20260818-3.htm">İlan</a>
    """
    assert [item.url for item in parse_fihrist(html, "2026-08-18")] == [
        "https://www.resmigazete.gov.tr/eskiler/2026/08/20260818-1.htm",
        "https://www.resmigazete.gov.tr/eskiler/2026/08/20260818-2.pdf",
    ]


def test_parse_fihrist_rejects_same_path_on_untrusted_host():
    html = '<a href="https://evil.example/eskiler/2026/08/20260818-1.pdf">Sahte</a>'
    assert parse_fihrist(html, "2026-08-18") == []
