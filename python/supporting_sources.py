from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

TARIFF_URL = "https://tariff.singlewindow.io/api/v2-0/tariff-query/notification-details/latest"
RG_OZETI_BASE = "https://www.resmigazeteozeti.com"


class ExplanationParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.links: list[dict[str, str]] = []
        self._href: str | None = None
        self._link_text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in {"p", "li", "br", "tr", "h1", "h2", "h3"}:
            self.parts.append(" ")
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._link_text = []

    def handle_data(self, data):
        if data.strip():
            self.parts.append(data)
        if self._href is not None:
            self._link_text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            self.links.append({
                "text": " ".join("".join(self._link_text).split()),
                "url": self._href,
            })
            self._href = None
            self._link_text = []

    def text(self) -> str:
        return " ".join(" ".join(self.parts).split())


def normalize_tariff_notice(item: dict, language: str = "TR") -> dict:
    messages = item.get("notification_messages") or []
    message = next(
        (m for m in messages if str(m.get("language_code", "")).upper() == language),
        messages[0] if messages else {},
    )
    raw_html = message.get("formatted_text") or message.get("text") or ""
    parser = ExplanationParser()
    parser.feed(raw_html)
    codes = sorted({
        str(detail.get("commodity_code"))
        for detail in item.get("details") or []
        if detail.get("commodity_code")
    })
    return {
        "source": "tariff",
        "source_classification": "SUPPORTING_NON_AUTHORITATIVE",
        "date": str(item.get("created_at") or "")[:10],
        "created_at": item.get("created_at"),
        "title": " ".join(str(message.get("title") or item.get("title") or "").split()),
        "event_code": item.get("event_code"),
        "source_country": (item.get("payload") or {}).get("data_source") or "",
        "explanation_html": raw_html,
        "explanation_text": parser.text(),
        "links": parser.links,
        "gtip_codes": codes,
    }


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
            text = " ".join(anchor.get_text(" ", strip=True).split())
            if "resmigazete.gov.tr" in url and "Resm" in text:
                official_url = url
            elif url.startswith(RG_OZETI_BASE + "/madde/") and not detail_url:
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


def fetch_supporting_sources(date: str, out_dir: Path, headers: dict | None = None) -> dict:
    raw_dir = out_dir / "raw" / "supporting"
    raw_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    if headers:
        session.headers.update(headers)

    result = {
        "policy": {
            "authoritative_source": "resmigazete.gov.tr",
            "supporting_sources_must_not_be_used_as_legal_evidence": True,
        },
        "tariff": {"status": "ok", "items": []},
        "resmi_gazete_ozeti": {"status": "ok", "items": []},
    }

    try:
        response = session.get(TARIFF_URL, timeout=30)
        response.raise_for_status()
        payload = response.json()
        (raw_dir / "tariff-latest.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        result["tariff"]["items"] = [
            normalize_tariff_notice(item)
            for item in payload
            if str(item.get("created_at") or "").startswith(date)
        ]
    except Exception as exc:
        result["tariff"]["status"] = f"error:{type(exc).__name__}:{exc}"

    try:
        url = f"{RG_OZETI_BASE}/tarih/{date}"
        response = session.get(url, timeout=25)
        response.raise_for_status()
        markup = response.text
        (raw_dir / "resmi-gazete-ozeti.html").write_text(markup, encoding="utf-8")
        result["resmi_gazete_ozeti"]["items"] = parse_rg_ozeti(markup, date)
    except Exception as exc:
        result["resmi_gazete_ozeti"]["status"] = f"error:{type(exc).__name__}:{exc}"

    (out_dir / "supporting-sources.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result
