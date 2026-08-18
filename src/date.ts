const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

export function resolveTargetDate(input?: string): string {
  if (input) {
    if (!DATE_RE.test(input)) {
      throw new Error(`Invalid date: ${input}. Expected YYYY-MM-DD.`);
    }
    return input;
  }

  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Europe/Istanbul',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date());
}

export function buildDailyIndexUrl(date: string): string {
  if (!DATE_RE.test(date)) {
    throw new Error(`Invalid date: ${date}. Expected YYYY-MM-DD.`);
  }
  const [year, month, day] = date.split('-');
  return `https://www.resmigazete.gov.tr/eskiler/${year}/${month}/${year}${month}${day}.htm`;
}
