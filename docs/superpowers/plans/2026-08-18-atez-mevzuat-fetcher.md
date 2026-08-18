# ATEZ Mevzuat Fetcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a daily GitHub Actions fetcher that retrieves official Resmî Gazete sources, probes mevzuat.gov.tr, preserves raw evidence, emits detailed manifests/logs, and optionally uploads outputs to Google Drive.

**Architecture:** TypeScript modules separate date/URL generation, HTTP/Playwright fetching, Resmî Gazete parsing, manifest persistence, and Google Drive upload. GitHub Actions runs tests first, then the fetcher, then always stores the `out/` directory as an Actions artifact; Drive upload is enabled only when its service-account secret is present.

**Tech Stack:** Node.js 22, TypeScript, Vitest, Playwright Chromium, Cheerio, googleapis, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-18-atez-mevzuat-fetcher-design.md`

## Global Constraints

- GitHub repository remains private.
- Daily schedule is 04:00 UTC (07:00 Europe/Istanbul).
- Raw official-source bytes must be preserved unchanged.
- Third-party discovery pages are not legal evidence and are not required by this fetcher.
- Every failed direct fetch remains visible even if browser fallback succeeds.
- Missing exact official content produces a partial/blocked result, never fabricated content.
- Google credentials are secret-only and never committed.

---

### Task 1: Core URL/date and discovery parsing

**Files:**
- Create: `src/date.ts`
- Create: `src/resmi-gazete.ts`
- Test: `tests/date.test.ts`
- Test: `tests/resmi-gazete.test.ts`

**Interfaces:**
- Produces: `resolveTargetDate(input?: string): string`
- Produces: `buildDailyIndexUrl(date: string): string`
- Produces: `parseOfficialDocumentLinks(html: string, baseUrl: string, date: string): OfficialDocument[]`

- [ ] Write failing tests for Istanbul-date resolution, historical index URL generation, and filtering/uniquing official daily document links.
- [ ] Run `npm test` and verify failures are caused by missing implementation modules.
- [ ] Implement the minimal functions.
- [ ] Run `npm test` and verify Task 1 passes.

### Task 2: Fetch with HTTP-first and Playwright fallback

**Files:**
- Create: `src/fetch-resource.ts`
- Create: `src/types.ts`
- Test: `tests/fetch-resource.test.ts`

**Interfaces:**
- Produces: `fetchResource(url, options): Promise<FetchOutcome>`
- `FetchOutcome` records all attempts, chosen method, raw bytes, status, content type, final URL, timestamps and error/fallback reason.

- [ ] Write failing tests using injected HTTP/browser fetch functions so real network is not required.
- [ ] Verify the tests fail before implementation.
- [ ] Implement HTTP-first behavior, unusable-response detection, browser fallback for HTML, and attempt logging.
- [ ] Verify tests pass.

### Task 3: Run orchestration and manifests

**Files:**
- Create: `src/run.ts`
- Create: `src/io.ts`
- Create: `src/index.ts`
- Test: `tests/run.test.ts`

**Interfaces:**
- Consumes Task 1 and Task 2 APIs.
- Produces `out/YYYY-MM-DD/discovery-manifest.json`, `fetch-manifest.json`, `fetch-log.txt`, and `raw/*`.

- [ ] Write failing orchestration tests against temporary directories and injected fetcher.
- [ ] Verify red state.
- [ ] Implement daily-index fetch, parsing, per-document fetch, mevzuat.gov.tr probe, raw-file persistence, and overall PASS/PARTIAL/BLOCKED status.
- [ ] Verify tests pass.

### Task 4: Optional Google Drive upload

**Files:**
- Create: `src/google-drive.ts`
- Test: `tests/google-drive.test.ts`

**Interfaces:**
- Produces: `uploadRunToDrive(options): Promise<DriveUploadSummary>`.
- Creates/reuses `runs/YYYY-MM-DD/sources`, `runs/YYYY-MM-DD/sources/raw`, and `runs/YYYY-MM-DD/logs` under configured ATEZ root.

- [ ] Write failing tests with a fake Drive adapter covering find-or-create folder logic and deterministic destination paths.
- [ ] Verify red state.
- [ ] Implement service-account-backed Google Drive adapter and optional no-secret skip behavior.
- [ ] Verify tests pass.

### Task 5: GitHub Actions and operational docs

**Files:**
- Create: `.github/workflows/daily.yml`
- Create: `README.md`

**Interfaces:**
- Scheduled run at `0 4 * * *` plus `workflow_dispatch` with optional `date` input.
- Always uploads `out/` as an Actions artifact.
- Drive upload receives only `GDRIVE_SERVICE_ACCOUNT_JSON` and `GDRIVE_ROOT_FOLDER_ID` secrets/env.

- [ ] Add workflow that installs Node dependencies and Playwright Chromium, runs tests, executes the fetcher, optionally uploads to Drive, and always uploads artifacts.
- [ ] Document setup, secrets, manual backfill command, output contract and source-fallback behavior.
- [ ] Open a draft PR and inspect Actions results.
- [ ] Fix any CI/runtime failures and verify a manual/current-day network probe produces an artifact.
