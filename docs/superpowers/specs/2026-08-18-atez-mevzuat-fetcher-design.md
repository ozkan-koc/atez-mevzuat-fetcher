# ATEZ Mevzuat Fetcher — Design

## Goal
Build a zero-cost daily fetcher that runs in GitHub Actions, retrieves the current Resmî Gazete publication set and probes mevzuat.gov.tr, saves raw HTML/PDF plus detailed machine-readable logs, and optionally uploads the run into the existing Google Drive ATEZ-Mevzuat-Radari structure.

## Architecture
- Runtime: GitHub Actions on ubuntu-latest.
- Language: Node.js + TypeScript.
- Fetch strategy: normal `fetch()` first; Playwright/Chromium fallback for HTML when normal fetch fails or returns an unusable response.
- Sources: `resmigazete.gov.tr` daily index + resolved document URLs, and `mevzuat.gov.tr` reachability/content probe.
- Output: `out/YYYY-MM-DD/` with `discovery-manifest.json`, `fetch-manifest.json`, `fetch-log.txt`, and `raw/` files.
- Google Drive: optional upload when `GDRIVE_SERVICE_ACCOUNT_JSON` is configured. Target root defaults to the existing ATEZ-Mevzuat-Radari folder ID and creates/uses `runs/YYYY-MM-DD/sources` and `logs`.
- GitHub artifact upload always runs so a failed Drive upload never loses fetched evidence.

## Logging contract
Every request records: source URL, source type, method (`fetch` or `playwright`), started/finished timestamps, HTTP status when available, final URL, content type, byte count, local output path, success/failure, fallback reason, and error text.

## Safety and correctness
- Third-party discovery sources are not used by the fetcher as legal evidence.
- The fetcher does not perform AI analysis or legal classification.
- Raw official source bytes are preserved as received.
- A failed direct request is visible in the manifest even when Playwright succeeds.
- If exact official content cannot be fetched, the run is marked partial/blocked rather than inventing data.

## Schedule
GitHub cron runs daily at 04:00 UTC, equivalent to 07:00 Europe/Istanbul. Manual workflow dispatch accepts an optional `date` (`YYYY-MM-DD`) for backfills/tests.

## Google Drive authentication
Use a Google service account JSON stored only in GitHub Actions secret `GDRIVE_SERVICE_ACCOUNT_JSON`. The service-account email must be granted access to the existing Drive root folder. No credential is committed to the repository.
