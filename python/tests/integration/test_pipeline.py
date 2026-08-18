import json

from atez_collector.pipeline import run


class FakeResponse:
    def __init__(self, url, content, content_type="text/html"):
        self.url = url
        self.content = content
        self.headers = {"content-type": content_type}
        self.status_code = 200
        self.ok = True

    @property
    def text(self):
        return self.content.decode()


class FakeSession:
    headers = {}

    def get(self, url, timeout, allow_redirects=True, verify=True):
        if url.endswith("18.08.2026"):
            return FakeResponse(url, b'<html><a href="/eskiler/2026/08/20260818-1.pdf">Belge</a></html>')
        return FakeResponse(url, b"%PDF-1.7\nbody", "application/pdf")


def no_supporting(date, out_dir, headers):
    result = {
        "policy": {"supporting_sources_must_not_be_used_as_legal_evidence": True},
        "tariff": {"status": "skipped", "items": []},
        "resmi_gazete_ozeti": {"status": "skipped", "items": []},
    }
    (out_dir / "supporting-sources.json").write_text(json.dumps(result))
    return result


def test_run_writes_versioned_manifest_and_verified_inventory(tmp_path):
    code = run(
        "2026-08-18",
        output_root=tmp_path,
        session=FakeSession(),
        supporting_fetcher=no_supporting,
        sleep=lambda _: None,
    )
    manifest = json.loads((tmp_path / "2026-08-18" / "manifest.json").read_text())
    assert code == 0
    assert manifest["schema_version"] == "1.0"
    assert manifest["artifact_version"] == "atez-collector/v1"
    assert manifest["status"] == "PASS"
    official = [x for x in manifest["inventory"] if x["role"] == "official_evidence"]
    assert len(official) == 2  # index and one document
    assert all(len(x["sha256"]) == 64 for x in manifest["inventory"])
