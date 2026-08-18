import * as cheerio from 'cheerio';
import type { OfficialDocument } from './types.js';

export function parseOfficialDocumentLinks(
  html: string,
  baseUrl: string,
  date: string,
): OfficialDocument[] {
  const compactDate = date.replaceAll('-', '');
  const pattern = new RegExp(`/${compactDate}-(\\d+)\\.(htm|pdf)$`, 'i');
  const $ = cheerio.load(html);
  const seen = new Set<string>();
  const documents: OfficialDocument[] = [];

  $('a[href]').each((_, element) => {
    const href = $(element).attr('href');
    if (!href) return;

    let url: URL;
    try {
      url = new URL(href, baseUrl);
    } catch {
      return;
    }

    if (url.hostname !== 'www.resmigazete.gov.tr') return;
    const match = url.pathname.match(pattern);
    if (!match || seen.has(url.href)) return;

    seen.add(url.href);
    const fileName = url.pathname.split('/').at(-1)!;
    documents.push({
      id: `${compactDate}-${match[1]}`,
      url: url.href,
      fileName,
      extension: match[2]!.toLowerCase() as 'htm' | 'pdf',
    });
  });

  return documents;
}
