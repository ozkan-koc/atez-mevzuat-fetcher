import { resolveTargetDate } from './date.js';
import { runDailyFetch } from './run.js';

const explicitDate = process.env.TARGET_DATE || process.argv[2];
const date = resolveTargetDate(explicitDate || undefined);
const outRoot = process.env.OUT_ROOT || 'out';

const summary = await runDailyFetch({ date, outRoot });
console.log(JSON.stringify(summary, null, 2));

if (summary.status === 'BLOCKED') {
  process.exitCode = 2;
}
