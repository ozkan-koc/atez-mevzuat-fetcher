# ATEZ Collector v1 — Implementation record

- [x] Establish a single Python production path.
- [x] Split configuration, HTTP, official discovery/download/validation, supporting adapters, artifact handling, manifest creation, pipeline, and CLI.
- [x] Reject untrusted hosts and invalid HTML/PDF payloads.
- [x] Replace per-date output atomically and prevent stale files.
- [x] Add manifest schema/artifact versions and SHA-256 inventory.
- [x] Preserve a thin `rg_fetch.py` compatibility entrypoint.
- [x] Add unit and integration tests without live-network dependency.
- [x] Align GitHub Actions and operational documentation.
- [x] Remove the unused TypeScript/Playwright/Google Drive implementation.

Release boundary: GitHub returns the collector artifact; downstream scheduled-task skills own Drive archival, evidence analysis, publishing/revisions, and delivery.
