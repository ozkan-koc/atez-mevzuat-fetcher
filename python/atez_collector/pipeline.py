from __future__ import annotations

import json
import time
from pathlib import Path

import requests

from .artifact import ArtifactWorkspace
from .config import HEADERS, OUTPUT_ROOT
from .manifest import create_manifest
from .official.discovery import build_candidate_urls, parse_fihrist
from .official.downloader import download_official
from .supporting import fetch_supporting_sources


def run(
    date: str,
    *,
    output_root: Path = OUTPUT_ROOT,
    session=None,
    supporting_fetcher=fetch_supporting_sources,
    sleep=time.sleep,
) -> int:
    build_candidate_urls(date)  # validates YYYY-MM-DD
    session = session or requests.Session()
    session.headers.update(HEADERS)
    logs: list[dict] = []
    selected_source_url = None
    items = []
    verify_tls = True

    with ArtifactWorkspace(output_root, date) as workspace:
        assert workspace.path is not None
        for candidate in build_candidate_urls(date):
            response, record = download_official(session, candidate, verify_tls=verify_tls)
            logs.append(record)
            print(json.dumps(record, ensure_ascii=False), flush=True)
            if response is None:
                continue
            if record.get("tls_verification") is False:
                verify_tls = False
            parsed = parse_fihrist(response.text, date)
            record["fihrist_items_found"] = len(parsed)
            if not parsed:
                continue
            selected_source_url = candidate
            items = parsed
            workspace.write_bytes("raw/official/fihrist.html", response.content)
            break

        documents = []
        for item in items:
            response, record = download_official(session, item.url, verify_tls=verify_tls)
            logs.append(record)
            print(json.dumps(record, ensure_ascii=False), flush=True)
            fetched = response is not None
            if fetched:
                workspace.write_bytes(f"raw/official/{item.filename}", response.content)
            documents.append({**item.to_dict(), "fetched": fetched, "fetch": record})
            sleep(0.75)

        supporting = supporting_fetcher(date, workspace.path, HEADERS)
        official_complete = bool(items) and all(item["fetched"] for item in documents)
        status = "PASS" if official_complete else "BLOCKED"
        manifest = create_manifest(
            date=date,
            status=status,
            selected_source_url=selected_source_url,
            candidate_urls=build_candidate_urls(date),
            documents=documents,
            requests=logs,
            supporting=supporting,
            root=workspace.path,
        )
        workspace.write_json("manifest.json", manifest)
        print(json.dumps({
            "date": date,
            "status": status,
            "documents_discovered": manifest["documents_discovered"],
            "documents_fetched": manifest["documents_fetched"],
        }, ensure_ascii=False), flush=True)
    return 0 if status == "PASS" else 2
