import { describe, expect, it } from 'vitest';
import { buildDailyIndexUrl, resolveTargetDate } from '../src/date.js';
import { parseOfficialDocumentLinks } from '../src/resmi-gazete.js';
import { fetchResource } from '../src/fetch-resource.js';

describe('date helpers', () => {
  it('builds the historical Resmî Gazete daily index URL', () => {
    expect(buildDailyIndexUrl('2026-08-18')).toBe(
      'https://www.resmigazete.gov.tr/eskiler/2026/08/20260818.htm',
    );
  });

  it('preserves an explicitly supplied YYYY-MM-DD date', () => {
    expect(resolveTargetDate('2026-08-18')).toBe('2026-08-18');
  });
});

describe('official document discovery', () => {
  it('extracts only unique same-day official HTML/PDF document links', () => {
    const html = `
      <a href="20260818-1.htm">Law</a>
      <a href="/eskiler/2026/08/20260818-2.pdf">Decision</a>
      <a href="20260818-1.htm">Duplicate</a>
      <a href="20260817-9.pdf">Yesterday</a>
      <a href="other.html">Other</a>
    `;
    expect(
      parseOfficialDocumentLinks(
        html,
        'https://www.resmigazete.gov.tr/eskiler/2026/08/20260818.htm',
        '2026-08-18',
      ).map((item) => item.url),
    ).toEqual([
      'https://www.resmigazete.gov.tr/eskiler/2026/08/20260818-1.htm',
      'https://www.resmigazete.gov.tr/eskiler/2026/08/20260818-2.pdf',
    ]);
  });
});

describe('fetch fallback', () => {
  it('uses browser fallback when direct HTTP fetch fails and keeps both attempts in the log', async () => {
    const result = await fetchResource('https://example.test/page', {
      httpFetch: async () => {
        throw new Error('direct failed');
      },
      browserFetch: async () => ({
        status: 200,
        finalUrl: 'https://example.test/page',
        contentType: 'text/html; charset=utf-8',
        bytes: Buffer.from('<html>ok</html>'),
      }),
      allowBrowserFallback: true,
    });

    expect(result.success).toBe(true);
    expect(result.method).toBe('playwright');
    expect(result.attempts).toHaveLength(2);
    expect(result.attempts[0]?.success).toBe(false);
    expect(result.attempts[1]?.success).toBe(true);
    expect(result.bytes.toString()).toContain('ok');
  });
});
