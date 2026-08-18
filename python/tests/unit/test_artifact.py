import hashlib
import json

from atez_collector.artifact import ArtifactWorkspace, build_inventory


def test_workspace_replaces_stale_date_directory(tmp_path):
    target = tmp_path / "2026-08-18"
    target.mkdir()
    (target / "stale.txt").write_text("old")

    with ArtifactWorkspace(tmp_path, "2026-08-18") as workspace:
        workspace.write_bytes("raw/new.htm", b"<html>new</html>")

    assert not (target / "stale.txt").exists()
    assert (target / "raw/new.htm").exists()


def test_inventory_contains_hash_size_and_role(tmp_path):
    path = tmp_path / "raw" / "official" / "doc.pdf"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"%PDF-test")
    inventory = build_inventory(tmp_path)
    assert inventory == [{
        "path": "raw/official/doc.pdf",
        "role": "official_evidence",
        "media_type": "application/pdf",
        "bytes": 9,
        "sha256": hashlib.sha256(b"%PDF-test").hexdigest(),
    }]
