import { writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { buildDailyIndexUrl } from './date.js';
import { fetchResource } from './fetch-resource.js';
import { ensureDirectory, outcomeLogLines, outcomeRecord, writeBytes, writeJson } from './io.js';
import { parseOfficialDocumentLinks } from './resmi-gazete.js';
import type { FetchOutcome } from './types.js';

export interface RunDailyFetchOptions {
  date: string;
  outRoot?: string;
  fetcher?: (url: string, options?: { allowBrowserFallback?: boolean }) => Promise<FetchOutcome>;
}

export interface RunSummary {
  date: string;
  status: 'PASS' | 'BLOCKED';
  documentsDiscovered: number;
  documentsFetched: number;
  mevzuatProbeSuccess: boolean;
  runDir: string;
}

export async function runDailyFetch(options: RunDailyFetchOptions): Promise<RunSummary> {
  const outRoot = options.outRoot ?? 'out';
  const runDir = join(outRoot, options.date);
  const rawDir = join(runDir, 'raw');
  const fetcher = options.fetcher ?? fetchResource;
  const indexUrl = buildDailyIndexUrl(options.date);
  const logs: string[] = [`ATEZ Mevzuat Fetcher`, `date=${options.date}`, `started=${new Date().toISOString()}`];
  const resources: unknown[] = [];

  await ensureDirectory(rawDir);

  const indexOutcome = await fetcher(indexUrl, { allowBrowserFallback: true });
  logs.push(...outcomeLogLines('resmi-gazete-index', indexOutcome));
  let documents = [] as ReturnType<typeof parseOfficialDocumentLinks>;
  let indexOutputPath: string | undefined;

  if (indexOutcome.success) {
    indexOutputPath = join('raw', `${options.date.replaceAll('-', '')}-index.htm`);
    await writeBytes(join(runDir, indexOutputPath), indexOutcome.bytes);
    documents = parseOfficialDocumentLinks(indexOutcome.bytes.toString('utf8'), indexUrl, options.date);
  }
  resources.push(outcomeRecord(indexOutcome, indexOutputPath));

  await writeJson(join(runDir, 'discovery-manifest.json'), {
    schemaVersion: '1.0',
    date: options.date,
    indexUrl,
    indexFetchSuccess: indexOutcome.success,
    documents,
  });

  let documentsFetched = 0;
  for (const document of documents) {
    const outcome = await fetcher(document.url, { allowBrowserFallback: true });
    logs.push(...outcomeLogLines(`official-document:${document.id}`, outcome));
    let outputPath: string | undefined;
    if (outcome.success) {
      outputPath = join('raw', document.fileName);
      await writeBytes(join(runDir, outputPath), outcome.bytes);
      documentsFetched += 1;
    }
    resources.push(outcomeRecord(outcome, outputPath));
  }

  const mevzuatUrl = 'https://www.mevzuat.gov.tr/';
  const mevzuatOutcome = await fetcher(mevzuatUrl, { allowBrowserFallback: true });
  logs.push(...outcomeLogLines('mevzuat-home-probe', mevzuatOutcome));
  let mevzuatOutputPath: string | undefined;
  if (mevzuatOutcome.success) {
    mevzuatOutputPath = join('raw', 'mevzuat-home.htm');
    await writeBytes(join(runDir, mevzuatOutputPath), mevzuatOutcome.bytes);
  }
  resources.push(outcomeRecord(mevzuatOutcome, mevzuatOutputPath));

  const status: RunSummary['status'] =
    indexOutcome.success && documents.length > 0 && documentsFetched === documents.length
      ? 'PASS'
      : 'BLOCKED';

  await writeJson(join(runDir, 'fetch-manifest.json'), {
    schemaVersion: '1.0',
    date: options.date,
    status,
    documentsDiscovered: documents.length,
    documentsFetched,
    mevzuatProbeSuccess: mevzuatOutcome.success,
    resources,
  });

  logs.push(
    `status=${status}`,
    `documents_discovered=${documents.length}`,
    `documents_fetched=${documentsFetched}`,
    `mevzuat_probe_success=${mevzuatOutcome.success}`,
    `finished=${new Date().toISOString()}`,
  );
  await writeFile(join(runDir, 'fetch-log.txt'), `${logs.join('\n')}\n`, 'utf8');

  return {
    date: options.date,
    status,
    documentsDiscovered: documents.length,
    documentsFetched,
    mevzuatProbeSuccess: mevzuatOutcome.success,
    runDir,
  };
}
