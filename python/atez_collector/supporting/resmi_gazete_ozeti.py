from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

RG_OZETI_BASE = "https://www.resmigazeteozeti.com"


def parse_rg_ozeti(markup: str, date: str, area: str = "ticaret-gumruk") -> list[dict]:
    soup = BeautifulSoup(markup, "html.parser")
    items: list[dict] = []
    for article in soup.select("article.item"):
        areas = [x for x in (article.get("data-areas") or "").split(",") if x]
        if area not in areas:
            continue
        title_node = article.select_one(".item-title")
        summary_node = article.select_one(".item-summary")
        official_url = ""
        detail_url = ""
        for anchor in article.select("a[href]"):
            url = urljoin(RG_OZETI_BASE, anchor.get("href"))
            parsed = urlparse(url)
            text = " ".join(anchor.get_text(" ", strip=True).split())
            if parsed.hostname in {"resmigazete.gov.tr", "www.resmigazete.gov.tr"} and "Resm" in text:
                official_url = url
            elif url.startswith(f"{RG_OZETI_BASE}/madde/") and not detail_url:
                detail_url = url
        items.append({
            "source": "resmi_gazete_ozeti",
            "source_classification": "DISCOVERY_SUPPORTING_NON_AUTHORITATIVE",
            "date": date,
            "title": " ".join((title_node.get_text(" ", strip=True) if title_node else "").split()),
            "summary": " ".join((summary_node.get_text(" ", strip=True) if summary_node else "").split()),
            "interest_areas": areas,
            "official_url": official_url,
            "detail_url": detail_url,
        })
    return items


def fetch_resmi_gazete_ozeti(session, date: str, raw_dir: Path) -> dict:
    result = {"status": "ok", "items": []}
    try:
        response = session.get(f"{RG_OZETI_BASE}/tarih/{date}", timeout=25)
        response.raise_for_status()
        (raw_dir / "resmi-gazete-ozeti.html").write_text(response.text, encoding="utf-8")
        result["items"] = parse_rg_ozeti(response.text, date)
    except Exception as exc:
        result["status"] = f"error:{type(exc).__name__}:{exc}"
    return result
