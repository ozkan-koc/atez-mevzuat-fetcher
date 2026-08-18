from urllib.parse import urlparse

from ..config import OFFICIAL_HOSTS


class ValidationError(ValueError):
    pass


def validate_official_payload(url: str, content_type: str, content: bytes) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in OFFICIAL_HOSTS:
        raise ValidationError("response host is not an allowed official host")
    if not content:
        raise ValidationError("response body is empty")

    media_type = content_type.partition(";")[0].strip().lower()
    suffix = parsed.path.lower().rsplit("/", 1)[-1]
    if suffix.endswith(".pdf"):
        if not content.startswith(b"%PDF-"):
            raise ValidationError("missing PDF signature")
        if media_type and media_type not in {"application/pdf", "application/octet-stream"}:
            raise ValidationError(f"unexpected PDF content type: {media_type}")
        return

    sample = content[:4096].lstrip().lower()
    if b"<html" not in sample and b"<!doctype html" not in sample:
        raise ValidationError("missing HTML signature")
    if media_type and media_type not in {"text/html", "application/xhtml+xml"}:
        raise ValidationError(f"unexpected HTML content type: {media_type}")
