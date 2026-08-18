import { mkdir, writeFile } from 'node:fs/promises';
import { dirname } from 'node:path';
import type { FetchOutcome } from './types.js';

export async function ensureDirectory(path: string): Promise<void> {
  await mkdir(path, { recursive: true });
}

export async function writeJson(path: string, value: unknown): Promise<void> {
  await ensureDirectory(dirname(path));
  await writeFile(path, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

export async function writeBytes(path: string, bytes: Buffer): Promise<void> {
  await ensureDirectory(dirname(path));
  await writeFile(path, bytes);
}

export function outcomeRecord(outcome: FetchOutcome, outputPath?: string) {
  return {
    url: outcome.url,
    success: outcome.success,
    method: outcome.method,
    status: outcome.status,
    finalUrl: outcome.finalUrl,
    contentType: outcome.contentType,
    byteCount: outcome.bytes.length,
    outputPath,
    fallbackReason: outcome.fallbackReason,
    attempts: outcome.attempts,
  };
}

export function outcomeLogLines(label: string, outcome: FetchOutcome): string[] {
  const lines = [`[RESOURCE] ${label}`, `url=${outcome.url}`, `success=${outcome.success}`];
  if (outcome.fallbackReason) lines.push(`fallback_reason=${outcome.fallbackReason}`);
  for (const [index, attempt] of outcome.attempts.entries()) {
    lines.push(
      `attempt=${index + 1} method=${attempt.method} success=${attempt.success} status=${attempt.status ?? 'n/a'} content_type=${attempt.contentType ?? 'n/a'} bytes=${attempt.byteCount ?? 0} started=${attempt.startedAt} finished=${attempt.finishedAt}${attempt.error ? ` error=${attempt.error}` : ''}`,
    );
  }
  return lines;
}
