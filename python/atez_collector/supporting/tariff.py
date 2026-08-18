import json
from html.parser import HTMLParser
from pathlib import Path

TARIFF_URL = "https://tariff.singlewindow.io/api/v2-0/tariff-query/notification-details/latest"


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
        "gtip_codes": sorted({
            str(detail["commodity_code"])
            for detail in item.get("details") or []
            if detail.get("commodity_code")
        }),
    }


def fetch_tariff(session, date: str, raw_dir: Path) -> dict:
    result = {"status": "ok", "items": []}
    try:
        response = session.get(TARIFF_URL, timeout=30)
        response.raise_for_status()
        payload = response.json()
        (raw_dir / "tariff-latest.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        result["items"] = [
            normalize_tariff_notice(item)
            for item in payload
            if str(item.get("created_at") or "").startswith(date)
        ]
    except Exception as exc:
        result["status"] = f"error:{type(exc).__name__}:{exc}"
    return result
