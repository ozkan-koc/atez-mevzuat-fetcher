export type FetchMethod = 'fetch' | 'playwright';

export interface FetchAttempt {
  method: FetchMethod;
  startedAt: string;
  finishedAt: string;
  success: boolean;
  status?: number;
  finalUrl?: string;
  contentType?: string;
  byteCount?: number;
  error?: string;
}

export interface BrowserFetchResult {
  status: number;
  finalUrl: string;
  contentType: string;
  bytes: Buffer;
}

export interface FetchOutcome {
  url: string;
  success: boolean;
  method?: FetchMethod;
  status?: number;
  finalUrl?: string;
  contentType?: string;
  bytes: Buffer;
  attempts: FetchAttempt[];
  fallbackReason?: string;
}

export interface OfficialDocument {
  id: string;
  url: string;
  fileName: string;
  extension: 'htm' | 'pdf';
}
