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


def test_rg_ozeti_keeps_trade_customs_items_from_legacy_markup():
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


def test_rg_ozeti_keeps_trade_customs_items_from_current_semantic_markup():
    markup = """
    <section class="daily-section">
      <div class="regulation-card">
        <span>Yeni</span>
        <h4><a href="/madde/ithalat-rejimi-karari-656">İthalat Rejimi Kararında Değişiklik</a></h4>
        <p>Maldivler menşeli ürünlerin ithalat vergileri güncellendi.</p>
        <nav>
          <a href="/alan/ticaret-gumruk">Ticaret, Gümrük &amp; Dış Ticaret</a>
          <a href="/alan/tarim-hayvancilik">Tarım &amp; Hayvancılık</a>
        </nav>
        <a href="https://www.resmigazete.gov.tr/eskiler/2026/08/20260819-1.pdf">Resmî Gazete'de oku →</a>
      </div>
      <div class="regulation-card">
        <h4><a href="/madde/universite-yonetmeligi-999">Üniversite Yönetmeliği</a></h4>
        <p>Eğitim alanında değişiklik.</p>
        <a href="/alan/egitim-yuksekogretim">Eğitim &amp; Yükseköğretim</a>
        <a href="https://www.resmigazete.gov.tr/eskiler/2026/08/20260819-2.htm">Resmî Gazete'de oku →</a>
      </div>
    </section>
    """
    items = parse_rg_ozeti(markup, "2026-08-19")
    assert len(items) == 1
    assert items[0]["title"] == "İthalat Rejimi Kararında Değişiklik"
    assert items[0]["summary"] == "Maldivler menşeli ürünlerin ithalat vergileri güncellendi."
    assert items[0]["interest_areas"] == ["ticaret-gumruk", "tarim-hayvancilik"]
    assert items[0]["detail_url"].endswith("/madde/ithalat-rejimi-karari-656")
    assert items[0]["official_url"].endswith("20260819-1.pdf")


def test_rg_ozeti_does_not_treat_featured_links_as_items():
    markup = """
    <ul class="featured"><li><a href="/madde/featured-1">Öne çıkan madde</a></li></ul>
    <div class="regulation-card">
      <h4><a href="/madde/actual-1">Gerçek Madde</a></h4>
      <p>Özet.</p>
      <a href="/alan/ticaret-gumruk">Ticaret, Gümrük &amp; Dış Ticaret</a>
      <a href="https://www.resmigazete.gov.tr/eskiler/2026/08/20260819-3.htm">Resmî Gazete'de oku →</a>
    </div>
    """
    items = parse_rg_ozeti(markup, "2026-08-19")
    assert [item["title"] for item in items] == ["Gerçek Madde"]
