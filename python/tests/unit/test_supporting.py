from atez_collector.supporting.resmi_gazete_ozeti import parse_rg_ozeti
from atez_collector.supporting.tariff import normalize_tariff_notice


def test_normalize_tariff_notice_extracts_text_links_and_codes():
    notice = normalize_tariff_notice({
        "created_at": "2026-08-18T07:08:00Z",
        "notification_messages": [{
            "language_code": "TR",
            "title": " Duyuru  Başlığı ",
            "formatted_text": '<p>Açıklama</p><a href="https://example.com/x">Kaynak</a>',
        }],
        "details": [{"commodity_code": "0306"}, {"commodity_code": "0306"}],
    })
    assert notice["title"] == "Duyuru Başlığı"
    assert notice["links"] == [{"text": "Kaynak", "url": "https://example.com/x"}]
    assert notice["gtip_codes"] == ["0306"]


def test_rg_ozeti_keeps_trade_customs_items():
    markup = """
    <article class="item" data-areas="ticaret-gumruk,vergi">
      <h3 class="item-title">Gümrük Düzenlemesi</h3>
      <p class="item-summary">Kısa özet</p>
      <a href="/madde/123">Detay</a>
      <a href="https://www.resmigazete.gov.tr/eskiler/2026/08/20260818-4.pdf">Resmî Gazete</a>
    </article>
    <article class="item" data-areas="egitim"><h3 class="item-title">Üniversite</h3></article>
    """
    items = parse_rg_ozeti(markup, "2026-08-18")
    assert len(items) == 1
    assert items[0]["official_url"].endswith("20260818-4.pdf")
