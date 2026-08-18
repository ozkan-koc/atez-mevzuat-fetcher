from datetime import datetime
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from ..config import OFFICIAL_BASE_URL, OFFICIAL_HOSTS
from ..models import DocumentRef


def build_candidate_urls(date: str) -> list[str]:
    dt = datetime.strptime(date, "%Y-%m-%d")
    return [
        f"{OFFICIAL_BASE_URL}/{dt:%d.%m.%Y}",
        f"{OFFICIAL_BASE_URL}/eskiler/{dt:%Y/%m}/{dt:%Y%m%d}.htm",
    ]


def parse_fihrist(html: str, date: str) -> list[DocumentRef]:
    dt = datetime.strptime(date, "%Y-%m-%d")
    expected_prefix = f"/eskiler/{dt:%Y/%m}/{dt:%Y%m%d}-"
    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.select("div.fihrist-item.mb-1 a[href]") or soup.select("a[href]")
    seen: set[str] = set()
    items: list[DocumentRef] = []
    for anchor in anchors:
        href = anchor.get("href")
        if not href:
            continue
        url = urljoin(OFFICIAL_BASE_URL, href)
        parsed = urlparse(url)
        filename = parsed.path.rsplit("/", 1)[-1]
        if parsed.scheme != "https" or parsed.hostname not in OFFICIAL_HOSTS:
            continue
        if not parsed.path.startswith(expected_prefix):
            continue
        if not filename.lower().endswith((".htm", ".html", ".pdf")):
            continue
        if url in seen:
            continue
        seen.add(url)
        items.append(DocumentRef(
            title=" ".join(anchor.get_text(" ", strip=True).split()),
            url=url,
            filename=filename,
        ))
    return items
