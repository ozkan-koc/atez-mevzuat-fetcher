from .validation import ValidationError, validate_official_payload
from ..http_client import request_with_log


def download_official(session, url: str, *, verify_tls: bool = True):
    response, record = request_with_log(session, url, verify_tls=verify_tls)
    if response is None or not record.get("success"):
        return None, record
    try:
        validate_official_payload(
            response.url,
            response.headers.get("content-type", ""),
            response.content,
        )
    except ValidationError as exc:
        record["success"] = False
        record["validation_error"] = str(exc)
        return None, record
    record["content_validated"] = True
    return response, record
