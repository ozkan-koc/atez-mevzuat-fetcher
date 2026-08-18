from __future__ import annotations

import time
from datetime import UTC, datetime

import requests
import urllib3

from .config import REQUEST_TIMEOUT_SECONDS

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _response_record(response: requests.Response, started: float, verify_tls: bool) -> dict:
    return {
        "success": response.ok and bool(response.content),
        "status": response.status_code,
        "final_url": response.url,
        "content_type": response.headers.get("content-type", ""),
        "bytes": len(response.content),
        "tls_verification": verify_tls,
        "elapsed_ms": round((time.monotonic() - started) * 1000),
    }


def request_with_log(session, url: str, *, verify_tls: bool = True):
    started = time.monotonic()
    record = {
        "url": url,
        "started_at": datetime.now(UTC).isoformat(timespec="milliseconds"),
        "method": "requests",
    }

    def request(verify: bool):
        return session.get(
            url,
            timeout=REQUEST_TIMEOUT_SECONDS,
            allow_redirects=True,
            verify=verify,
        )

    if not verify_tls:
        try:
            response = request(False)
            record.update(_response_record(response, started, False))
            record["fallback_reason"] = "known_certificate_chain_workaround"
            return response, record
        except Exception as exc:  # request boundary; error is evidence
            record.update({
                "success": False,
                "tls_verification": False,
                "fallback_reason": "known_certificate_chain_workaround",
                "error": f"{type(exc).__name__}: {exc}",
                "elapsed_ms": round((time.monotonic() - started) * 1000),
            })
            return None, record

    try:
        response = request(True)
        record.update(_response_record(response, started, True))
        return response, record
    except requests.exceptions.SSLError as exc:
        verified_error = f"{type(exc).__name__}: {exc}"
        try:
            response = request(False)
            record.update(_response_record(response, started, False))
            record.update({
                "fallback_reason": "ssl_certificate_verification_failed",
                "verified_tls_error": verified_error,
            })
            return response, record
        except Exception as fallback_exc:  # request boundary; error is evidence
            record.update({
                "success": False,
                "tls_verification": False,
                "fallback_reason": "ssl_certificate_verification_failed",
                "verified_tls_error": verified_error,
                "error": f"{type(fallback_exc).__name__}: {fallback_exc}",
                "elapsed_ms": round((time.monotonic() - started) * 1000),
            })
            return None, record
    except Exception as exc:  # request boundary; error is evidence
        record.update({
            "success": False,
            "tls_verification": True,
            "error": f"{type(exc).__name__}: {exc}",
            "elapsed_ms": round((time.monotonic() - started) * 1000),
        })
        return None, record
