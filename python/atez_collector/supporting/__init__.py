from pathlib import Path

import requests

from .resmi_gazete_ozeti import fetch_resmi_gazete_ozeti
from .tariff import fetch_tariff


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
        "tariff": fetch_tariff(session, date, raw_dir),
        "resmi_gazete_ozeti": fetch_resmi_gazete_ozeti(session, date, raw_dir),
    }
    (out_dir / "supporting-sources.json").write_text(
        __import__("json").dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result


__all__ = ["fetch_supporting_sources"]
