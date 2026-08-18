from supporting_sources import normalize_tariff_notice, parse_rg_ozeti


def test_normalize_tariff_notice_extracts_tr_text_links_and_codes():
    item = {
        "created_at": "2026-08-17T07:08:00Z",
        "event_code": "TEST",
        "payload": {"data_source": "TR"},
        "notification_messages": [
            {
                "language_code": "TR",
                "title": "  Duyuru   Başlığı ",
                "formatted_text": '<p>Açıklama</p><a href="https://example.com/x">Kaynak</a>',
            }
        ],
        "details": [
            {"commodity_code": "030633100000"},
            {"commodity_code": "030633100000"},
            {"commodity_code": "160414210000"},
        ],
    }

    notice = normalize_tariff_notice(item)

    assert notice["source"] == "tariff"
    assert notice["date"] == "2026-08-17"
    assert notice["title"] == "Duyuru Başlığı"
    assert notice["explanation_text"] == "Açıklama Kaynak"
    assert notice["links"] == [{"text": "Kaynak", "url": "https://example.com/x"}]
    assert notice["gtip_codes"] == ["030633100000", "160414210000"]


def test_parse_rg_ozeti_keeps_only_trade_customs_items_and_official_urls():
    markup = '''
    <article class="item" data-areas="ticaret-gumruk,vergi">
      <h3 class="item-title"> Gümrük Düzenlemesi </h3>
      <p class="item-summary"> Kısa özet </p>
      <a href="/madde/123">Detay</a>
      <a href="https://www.resmigazete.gov.tr/eskiler/2026/08/20260817-4.pdf">Resmî Gazete</a>
    </article>
    <article class="item" data-areas="egitim">
      <h3 class="item-title"> Üniversite </h3>
      <p class="item-summary"> Eğitim </p>
    </article>
    '''

    items = parse_rg_ozeti(markup, "2026-08-17")

    assert len(items) == 1
    assert items[0]["title"] == "Gümrük Düzenlemesi"
    assert items[0]["summary"] == "Kısa özet"
    assert items[0]["detail_url"] == "https://www.resmigazeteozeti.com/madde/123"
    assert items[0]["official_url"].endswith("20260817-4.pdf")
    assert items[0]["date"] == "2026-08-17"
