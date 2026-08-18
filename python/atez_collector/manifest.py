from datetime import UTC, datetime

from .artifact import build_inventory
from .config import ARTIFACT_VERSION, SCHEMA_VERSION


def create_manifest(*, date, status, selected_source_url, candidate_urls, documents, requests, supporting, root):
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_version": ARTIFACT_VERSION,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "date": date,
        "status": status,
        "selected_source_url": selected_source_url,
        "candidate_urls": candidate_urls,
        "source_policy": {
            "primary_legal_evidence": "resmigazete.gov.tr",
            "supporting_sources": ["tariff.singlewindow.io", "resmigazeteozeti.com"],
            "supporting_sources_are_not_legal_evidence": True,
        },
        "tls_policy": {
            "verified_first": True,
            "certificate_chain_workaround_used": any(
                record.get("tls_verification") is False for record in requests
            ),
            "warning": "TLS verification is disabled only after a logged certificate verification failure.",
        },
        "documents_discovered": len(documents),
        "documents_fetched": sum(1 for item in documents if item["fetched"]),
        "documents": documents,
        "requests": requests,
        "supporting_sources": {
            "tariff_status": supporting["tariff"]["status"],
            "tariff_items": len(supporting["tariff"]["items"]),
            "resmi_gazete_ozeti_status": supporting["resmi_gazete_ozeti"]["status"],
            "resmi_gazete_ozeti_items": len(supporting["resmi_gazete_ozeti"]["items"]),
        },
        "inventory": build_inventory(root),
    }
