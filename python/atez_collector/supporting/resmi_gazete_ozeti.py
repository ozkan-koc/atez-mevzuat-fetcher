from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

RG_OZETI_BASE = "https://www.resmigazeteozeti.com"
OFFICIAL_HOSTS = {"resmigazete.gov.tr", "www.resmigazete.gov.tr"}


def _clean(value: str) -> str:
    return " ".join(value.split())


def _area_slug(url: str) -> str | None:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) == 2 and parts[0] == "alan":
        return parts[1]
    return None


def _official_url(container) -> str:
    for anchor in container.select("a[href]"):
        url = urljoin(RG_OZETI_BASE, anchor.get("href"))
        if urlparse(url).hostname in OFFICIAL_HOSTS:
            return url
    return ""


def _detail_url(container) -> str:
    for anchor in container.select("a[href]"):
        url = urljoin(RG_OZETI_BASE, anchor.get("href"))
        if url.startswith(f"{RG_OZETI_BASE}/madde/"):
            return url
    return ""


def _areas(container) -> list[str]:
    values: list[str] = []
    for anchor in container.select("a[href]"):
        url = urljoin(RG_OZETI_BASE, anchor.get("href"))
        slug = _area_slug(url)
        if slug and slug not in values:
            values.append(slug)
    return values


def _semantic_container(detail_anchor):
    node = detail_anchor.parent
    for _ in range(6):
        if node is None or getattr(node, "name", None) in {"body", "html", "[document]"}:
            return None
        if _official_url(node) and _areas(node):
            return node
        node = node.parent
    return None


def _append_item(items: list[dict], seen: set[str], *, date: str, area: str | None,
                 title: str, summary: str, areas: list[str], official_url: str, detail_url: str) -> None:
    if area and area not in areas:
        return
    identity = detail_url or official_url or title
    if not identity or identity in seen:
        return
    seen.add(identity)
    items.append({
        "source": "resmi_gazete_ozeti",
        "source_classification": "DISCOVERY_SUPPORTING_NON_AUTHORITATIVE",
        "date": date,
        "title": _clean(title),
        "summary": _clean(summary),
        "interest_areas": areas,
        "official_url": official_url,
        "detail_url": detail_url,
    })


def parse_rg_ozeti(markup: str, date: str, area: str | None = "ticaret-gumruk") -> list[dict]:
    soup = BeautifulSoup(markup, "html.parser")
    items: list[dict] = []
    seen: set[str] = set()

    # Backward compatibility with the original card markup.
    for article in soup.select("article.item"):
        areas = [x for x in (article.get("data-areas") or "").split(",") if x]
        title_node = article.select_one(".item-title")
        summary_node = article.select_one(".item-summary")
        _append_item(
            items,
            seen,
            date=date,
            area=area,
            title=title_node.get_text(" ", strip=True) if title_node else "",
            summary=summary_node.get_text(" ", strip=True) if summary_node else "",
            areas=areas,
            official_url=_official_url(article),
            detail_url=_detail_url(article),
        )

    # Current site markup is semantic rather than tied to article.item/data-areas.
    # Real regulation entries expose a heading link to /madde/, one or more /alan/
    # links and an official resmigazete.gov.tr link in the same local container.
    for heading in soup.select("h1, h2, h3, h4, h5, h6"):
        detail_anchor = heading.select_one('a[href^="/madde/"], a[href^="https://www.resmigazeteozeti.com/madde/"]')
        if detail_anchor is None:
            continue
        container = _semantic_container(detail_anchor)
        if container is None:
            continue
        paragraphs = container.select("p")
        summary = paragraphs[0].get_text(" ", strip=True) if paragraphs else ""
        _append_item(
            items,
            seen,
            date=date,
            area=area,
            title=detail_anchor.get_text(" ", strip=True),
            summary=summary,
            areas=_areas(container),
            official_url=_official_url(container),
            detail_url=urljoin(RG_OZETI_BASE, detail_anchor.get("href")),
        )

    return items


def fetch_resmi_gazete_ozeti(session, date: str, raw_dir: Path) -> dict:
    result = {"status": "ok", "items": [], "page_items_detected": 0}
    try:
        response = session.get(f"{RG_OZETI_BASE}/tarih/{date}", timeout=25)
        response.raise_for_status()
        (raw_dir / "resmi-gazete-ozeti.html").write_text(response.text, encoding="utf-8")
        all_items = parse_rg_ozeti(response.text, date, area=None)
        result["page_items_detected"] = len(all_items)
        result["items"] = [item for item in all_items if "ticaret-gumruk" in item["interest_areas"]]
        if not all_items and "/madde/" in response.text:
            result["status"] = "parser_mismatch"
    except Exception as exc:
        result["status"] = f"error:{type(exc).__name__}:{exc}"
    return result
