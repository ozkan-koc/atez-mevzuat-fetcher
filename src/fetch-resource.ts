import { chromium } from 'playwright';
import type { BrowserFetchResult, FetchAttempt, FetchOutcome } from './types.js';

interface FetchResourceOptions {
  httpFetch?: (url: string) => Promise<BrowserFetchResult>;
  browserFetch?: (url: string) => Promise<BrowserFetchResult>;
  allowBrowserFallback?: boolean;
}

const HTTP_TIMEOUT_MS = 20_000;

async function defaultHttpFetch(url: string): Promise<BrowserFetchResult> {
  const response = await fetch(url, {
    redirect: 'follow',
    signal: AbortSignal.timeout(HTTP_TIMEOUT_MS),
    headers: {
      'user-agent':
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131 Safari/537.36',
      accept: 'text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8',
      'accept-language': 'tr-TR,tr;q=0.9,en;q=0.8',
    },
  });
  return {
    status: response.status,
    finalUrl: response.url,
    contentType: response.headers.get('content-type') ?? '',
    bytes: Buffer.from(await response.arrayBuffer()),
  };
}

async function defaultBrowserFetch(url: string): Promise<BrowserFetchResult> {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ locale: 'tr-TR' });
    const response = await page.goto(url, {
      waitUntil: 'domcontentloaded',
      timeout: 45_000,
    });
    if (!response) throw new Error('Browser navigation returned no response');
    const contentType = response.headers()['content-type'] ?? '';
    let bytes: Buffer;
    try {
      bytes = await response.body();
    } catch {
      if (!contentType.toLowerCase().includes('text/html')) throw new Error('Could not read browser response body');
      bytes = Buffer.from(await page.content(), 'utf8');
    }
    return {
      status: response.status(),
      finalUrl: response.url(),
      contentType,
      bytes,
    };
  } finally {
    await browser.close();
  }
}

function attemptFromResult(
  method: 'fetch' | 'playwright',
  startedAt: string,
  finishedAt: string,
  result: BrowserFetchResult,
): FetchAttempt {
  return {
    method,
    startedAt,
    finishedAt,
    success: result.status >= 200 && result.status < 400 && result.bytes.length > 0,
    status: result.status,
    finalUrl: result.finalUrl,
    contentType: result.contentType,
    byteCount: result.bytes.length,
  };
}

export async function fetchResource(
  url: string,
  options: FetchResourceOptions = {},
): Promise<FetchOutcome> {
  const httpFetch = options.httpFetch ?? defaultHttpFetch;
  const browserFetch = options.browserFetch ?? defaultBrowserFetch;
  const allowBrowserFallback = options.allowBrowserFallback ?? true;
  const attempts: FetchAttempt[] = [];
  let fallbackReason: string | undefined;

  const httpStartedAt = new Date().toISOString();
  try {
    const result = await httpFetch(url);
    const finishedAt = new Date().toISOString();
    const attempt = attemptFromResult('fetch', httpStartedAt, finishedAt, result);
    attempts.push(attempt);
    if (attempt.success) {
      return { url, success: true, method: 'fetch', ...result, attempts };
    }
    fallbackReason = `Direct fetch returned HTTP ${result.status}`;
  } catch (error) {
    fallbackReason = error instanceof Error ? error.message : String(error);
    attempts.push({
      method: 'fetch',
      startedAt: httpStartedAt,
      finishedAt: new Date().toISOString(),
      success: false,
      error: fallbackReason,
    });
  }

  if (allowBrowserFallback) {
    const browserStartedAt = new Date().toISOString();
    try {
      const result = await browserFetch(url);
      const finishedAt = new Date().toISOString();
      const attempt = attemptFromResult('playwright', browserStartedAt, finishedAt, result);
      attempts.push(attempt);
      if (attempt.success) {
        return {
          url,
          success: true,
          method: 'playwright',
          ...result,
          attempts,
          fallbackReason,
        };
      }
    } catch (error) {
      attempts.push({
        method: 'playwright',
        startedAt: browserStartedAt,
        finishedAt: new Date().toISOString(),
        success: false,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  return {
    url,
    success: false,
    bytes: Buffer.alloc(0),
    attempts,
    fallbackReason,
  };
}
