import { resolveTargetDate } from './date.js';
import { createGoogleDriveClientFromServiceAccount, uploadRunToDrive } from './google-drive.js';
import { runDailyFetch } from './run.js';

const explicitDate = process.env.TARGET_DATE || process.argv[2];
const date = resolveTargetDate(explicitDate || undefined);
const outRoot = process.env.OUT_ROOT || 'out';

const summary = await runDailyFetch({ date, outRoot });
console.log(JSON.stringify(summary, null, 2));

const serviceAccountJson = process.env.GDRIVE_SERVICE_ACCOUNT_JSON;
if (serviceAccountJson) {
  const rootFolderId = process.env.GDRIVE_ROOT_FOLDER_ID || '1AcOtFDbNn5b8JoRaFri1DjnjtY0C7W3N';
  const driveSummary = await uploadRunToDrive({
    client: createGoogleDriveClientFromServiceAccount(serviceAccountJson),
    rootFolderId,
    date,
    runDir: summary.runDir,
  });
  console.log(`Google Drive upload: ${JSON.stringify(driveSummary)}`);
} else {
  console.log('Google Drive upload skipped: GDRIVE_SERVICE_ACCOUNT_JSON is not configured.');
}

if (summary.status === 'BLOCKED') {
  process.exitCode = 2;
}
