import requests

from atez_collector.http_client import request_with_log


class FakeResponse:
    ok = True
    status_code = 200
    url = "https://www.resmigazete.gov.tr/18.08.2026"
    headers = {"content-type": "text/html"}
    content = b"<html>ok</html>"


class FakeSession:
    def __init__(self):
        self.verify_values = []

    def get(self, url, timeout, allow_redirects, verify):
        self.verify_values.append(verify)
        if verify:
            raise requests.exceptions.SSLError("certificate verify failed")
        return FakeResponse()


def test_tls_fallback_occurs_only_after_ssl_error():
    session = FakeSession()
    response, log = request_with_log(session, FakeResponse.url)
    assert response is not None
    assert session.verify_values == [True, False]
    assert log["success"] is True
    assert log["tls_verification"] is False
    assert log["fallback_reason"] == "ssl_certificate_verification_failed"
