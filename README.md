# ATEZ Mevzuat Fetcher

Zero-cost GitHub Actions fetcher for the ATEZ Mevzuat Radarı pipeline.

## What it does

For a target Turkey date (`YYYY-MM-DD`), the fetcher:

1. builds the official Resmî Gazete daily index URL,
2. tries a normal HTTP fetch,
3. falls back to Playwright/Chromium for HTML when needed,
4. discovers same-day official HTML/PDF document links,
5. downloads every discovered official document,
6. probes `https://www.mevzuat.gov.tr/` as an additional official-source availability signal,
7. writes detailed request attempts, manifests, and raw files under `out/YYYY-MM-DD/`,
8. optionally uploads the run to the existing Google Drive `ATEZ-Mevzuat-Radari` root.

The fetcher performs no AI analysis and does not treat a failed source as verified.

## Output

```text
out/YYYY-MM-DD/
  discovery-manifest.json
  fetch-manifest.json
  fetch-log.txt
  raw/
    YYYYMMDD-index.htm
    YYYYMMDD-1.htm
    YYYYMMDD-2.pdf
    ...
    mevzuat-home.htm
```

Each request attempt records the URL, method (`fetch` / `playwright`), timestamps, status code when available, final URL, content type, byte count, errors, and fallback reason.

## Local commands

```bash
npm install
npx playwright install chromium
npm test
npm run typecheck
npm run fetch -- 2026-08-18
```

Without a date, the CLI resolves the current date in `Europe/Istanbul`.

## GitHub Actions

`.github/workflows/daily.yml` runs every day at `04:00 UTC`, corresponding to `07:00 Europe/Istanbul`, and also supports manual workflow dispatch with an optional historical date.

The workflow always uploads `out/` as a GitHub Actions artifact, including blocked runs, so failed official-source attempts remain inspectable.

## Google Drive

Drive upload is optional. When no Drive secret is configured, fetching still runs and the Actions artifact is retained.

To enable Drive upload:

1. Create a Google Cloud service account with Google Drive API access.
2. Share the existing `ATEZ-Mevzuat-Radari` Drive root folder with the service-account email as an editor.
3. Add the service-account JSON to the repository Actions secret `GDRIVE_SERVICE_ACCOUNT_JSON`.
4. Optionally add `GDRIVE_ROOT_FOLDER_ID`. If omitted, the fetcher uses the existing ATEZ root folder ID configured in the CLI.

The uploader creates/reuses this minimum structure:

```text
ATEZ-Mevzuat-Radari/
  runs/
    YYYY-MM-DD/
      sources/
        discovery-manifest.json
        fetch-manifest.json
        raw/
      logs/
        fetch-log.txt
```

Credentials are never written to the repository or output manifests.

## Status behavior

- `PASS`: official Resmî Gazete daily index was retrieved, at least one same-day official document was discovered, and every discovered official document was fetched.
- `BLOCKED`: the index could not be retrieved, no official documents could be established, or at least one discovered official document could not be fetched.
- `mevzuat.gov.tr` probe status is logged independently and does not override the Resmî Gazete run status.

A browser fallback success does not hide a failed direct request; both attempts remain in `fetch-manifest.json` and `fetch-log.txt`.
