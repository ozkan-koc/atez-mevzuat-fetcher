import pytest

from atez_collector.official.validation import ValidationError, validate_official_payload


def test_accepts_pdf_signature():
    validate_official_payload(
        "https://www.resmigazete.gov.tr/eskiler/2026/08/20260818-1.pdf",
        "application/pdf",
        b"%PDF-1.7\nbody",
    )


def test_rejects_pdf_url_returning_html():
    with pytest.raises(ValidationError, match="PDF signature"):
        validate_official_payload(
            "https://www.resmigazete.gov.tr/eskiler/2026/08/20260818-1.pdf",
            "text/html",
            b"<html>error</html>",
        )


def test_rejects_redirect_to_untrusted_host():
    with pytest.raises(ValidationError, match="host"):
        validate_official_payload("https://evil.example/file.htm", "text/html", b"<html>ok</html>")
