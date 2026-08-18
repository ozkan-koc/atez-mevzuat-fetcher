# ATEZ Collector v1 — Architecture

## Responsibility

The repository is a deterministic evidence collector. GitHub Actions schedules it and returns an artifact. Downstream scheduled-task skills archive, analyze, publish, revise, and deliver; those concerns do not belong in this codebase.

## Modules

- `config.py`: stable runtime constants and source allowlists.
- `http_client.py`: request evidence and explicit TLS fallback logging.
- `official/discovery.py`: same-date official-link discovery.
- `official/validation.py`: final-host, content-type, and byte-signature checks.
- `official/downloader.py`: validated official downloads.
- `supporting/`: isolated Tariff and Resmî Gazete Özeti adapters.
- `artifact.py`: contained paths, atomic date replacement, hashes and inventory.
- `manifest.py`: versioned machine-readable contract.
- `pipeline.py`: orchestration only.
- `cli.py`: Istanbul-date CLI boundary.

## Trust model

`resmigazete.gov.tr` is authoritative. Supporting sources may aid discovery and later analysis but are never legal evidence. An HTTP 200 response is insufficient: the collector also verifies the final host and expected file signature. TLS verification is attempted first; the existing certificate-chain workaround is allowed only after a recorded verification error.

## Artifact

The immutable handoff unit is `out/YYYY-MM-DD/`. A rerun stages a fresh directory and replaces the prior date only after the new artifact is complete. `manifest.json` exists for `PASS` and `BLOCKED`, has schema and artifact versions, and inventories every other file with SHA-256.

## Excluded

No AI analysis, report HTML, Google Drive API, mail delivery, recipients, or credentials are implemented here.
