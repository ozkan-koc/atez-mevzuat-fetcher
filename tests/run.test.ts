import { mkdtemp, readFile, stat } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { runDailyFetch } from '../src/run.js';
import type { FetchOutcome } from '../src/types.js';

function success(url: string, contentType: string, body: string): FetchOutcome {
  const bytes = Buffer.from(body);
  return {
    url,
    success: true,
    method: 'fetch',
    status: 200,
    finalUrl: url,
    contentType,
    bytes,
    attempts: [
      {
        method: 'fetch',
        startedAt: '2026-08-18T04:00:00.000Z',
        finishedAt: '2026-08-18T04:00:01.000Z',
        success: true,
        status: 200,
        finalUrl: url,
        contentType,
        byteCount: bytes.length,
      },
    ],
  };
}

describe('daily run orchestration', () => {
  it('persists discovery, fetch manifest, logs and raw official bytes', async () => {
    const outRoot = await mkdtemp(join(tmpdir(), 'atez-fetcher-'));
    const indexUrl = 'https://www.resmigazete.gov.tr/eskiler/2026/08/20260818.htm';
    const htmlUrl = 'https://www.resmigazete.gov.tr/eskiler/2026/08/20260818-1.htm';
    const pdfUrl = 'https://www.resmigazete.gov.tr/eskiler/2026/08/20260818-2.pdf';

    const fetcher = async (url: string): Promise<FetchOutcome> => {
      if (url === indexUrl) {
        return success(
          url,
          'text/html',
          `<a href="20260818-1.htm">A</a><a href="20260818-2.pdf">B</a>`,
        );
      }
      if (url === htmlUrl) return success(url, 'text/html', '<html>law</html>');
      if (url === pdfUrl) return success(url, 'application/pdf', '%PDF-test');
      if (url === 'https://www.mevzuat.gov.tr/') {
        return success(url, 'text/html', '<html>mevzuat</html>');
      }
      throw new Error(`Unexpected URL ${url}`);
    };

    const summary = await runDailyFetch({ date: '2026-08-18', outRoot, fetcher });

    expect(summary.status).toBe('PASS');
    expect(summary.documentsDiscovered).toBe(2);
    expect(summary.documentsFetched).toBe(2);

    const runDir = join(outRoot, '2026-08-18');
    const discovery = JSON.parse(await readFile(join(runDir, 'discovery-manifest.json'), 'utf8'));
    const manifest = JSON.parse(await readFile(join(runDir, 'fetch-manifest.json'), 'utf8'));
    const log = await readFile(join(runDir, 'fetch-log.txt'), 'utf8');

    expect(discovery.documents.map((d: { url: string }) => d.url)).toEqual([htmlUrl, pdfUrl]);
    expect(manifest.status).toBe('PASS');
    expect(manifest.resources).toHaveLength(4); // index + 2 docs + mevzuat probe
    expect(log).toContain('resmigazete.gov.tr');
    expect(log).toContain('mevzuat.gov.tr');
    expect((await stat(join(runDir, 'raw', '20260818-1.htm'))).size).toBeGreaterThan(0);
    expect((await stat(join(runDir, 'raw', '20260818-2.pdf'))).size).toBeGreaterThan(0);
  });
});
