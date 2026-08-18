from __future__ import annotations

import hashlib
import mimetypes
import os
import shutil
import tempfile
from pathlib import Path, PurePosixPath


class ArtifactWorkspace:
    def __init__(self, output_root: Path, date: str):
        self.output_root = Path(output_root)
        self.date = date
        self.target = self.output_root / date
        self.path: Path | None = None

    def __enter__(self):
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.path = Path(tempfile.mkdtemp(prefix=f".{self.date}-", dir=self.output_root))
        return self

    def write_bytes(self, relative_path: str, content: bytes) -> Path:
        if self.path is None:
            raise RuntimeError("workspace is not open")
        safe = PurePosixPath(relative_path)
        if safe.is_absolute() or ".." in safe.parts:
            raise ValueError("artifact path must be relative and contained")
        destination = self.path.joinpath(*safe.parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        return destination

    def write_json(self, relative_path: str, value: dict) -> Path:
        import json
        return self.write_bytes(
            relative_path,
            json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8"),
        )

    def __exit__(self, exc_type, exc, traceback):
        if self.path is None:
            return
        if exc_type is not None:
            shutil.rmtree(self.path, ignore_errors=True)
            return
        backup = self.output_root / f".{self.date}.previous"
        if backup.exists():
            shutil.rmtree(backup)
        if self.target.exists():
            os.replace(self.target, backup)
        os.replace(self.path, self.target)
        shutil.rmtree(backup, ignore_errors=True)


def _role(relative: str) -> str:
    if relative.startswith("raw/official/"):
        return "official_evidence"
    if relative.startswith("raw/supporting/"):
        return "supporting_raw"
    if relative == "supporting-sources.json":
        return "supporting_normalized"
    return "run_metadata"


def build_inventory(root: Path) -> list[dict]:
    entries = []
    for path in sorted(Path(root).rglob("*")):
        if not path.is_file() or path.name == "manifest.json":
            continue
        content = path.read_bytes()
        relative = path.relative_to(root).as_posix()
        media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        entries.append({
            "path": relative,
            "role": _role(relative),
            "media_type": media_type,
            "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        })
    return entries
