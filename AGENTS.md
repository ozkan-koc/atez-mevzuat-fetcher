# Repository guide

## Scope

This repository only collects and packages evidence. It does not analyze legislation, generate reports, upload to Drive, or send email.

## Runtime

- The production path is Python under `python/atez_collector/`.
- Keep `python/rg_fetch.py` as a thin compatibility entrypoint.
- GitHub Actions is the scheduler and publishes `python/out/` as the run artifact.

## Source boundaries

- `resmigazete.gov.tr` is the sole authoritative legal-evidence source.
- Tariff and Resmî Gazete Özeti are supporting, non-authoritative sources.
- Supporting-source failure must be recorded but must not change an otherwise complete official run from `PASS`.
- Never accept official evidence after a redirect to an unapproved host.

## Artifact contract

- Output is `python/out/YYYY-MM-DD/`.
- `manifest.json` is mandatory for both `PASS` and `BLOCKED` runs.
- Preserve official bytes under `raw/official/`; supporting bytes belong under `raw/supporting/`.
- Every non-manifest file must appear in the manifest inventory with byte size, media type, role, and SHA-256.
- Writing a date must replace that date atomically so stale files cannot survive a rerun.

## Commands

```bash
cd python
python -m pip install -e ".[test]"
pytest
python rg_fetch.py 2026-08-18
```

Add or change tests before changing collector behavior. Do not add credentials, Drive IDs, recipients, report templates, or delivery logic to this repository.
