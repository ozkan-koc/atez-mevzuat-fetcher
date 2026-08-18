import { readFile, readdir } from 'node:fs/promises';
import { basename, extname, join } from 'node:path';
import { Readable } from 'node:stream';
import { google, type drive_v3 } from 'googleapis';

export interface DriveClient {
  findFolder(name: string, parentId: string): Promise<string | undefined>;
  createFolder(name: string, parentId: string): Promise<string>;
  uploadFile(input: {
    name: string;
    parentId: string;
    mimeType: string;
    body: Buffer;
  }): Promise<string>;
}

export interface DriveUploadSummary {
  uploadedFiles: number;
  dateFolderId: string;
  sourcesFolderId: string;
  rawFolderId: string;
  logsFolderId: string;
}

function escapeQueryValue(value: string): string {
  return value.replaceAll('\\', '\\\\').replaceAll("'", "\\'");
}

export function createGoogleDriveClientFromServiceAccount(serviceAccountJson: string): DriveClient {
  const credentials = JSON.parse(serviceAccountJson) as {
    client_email: string;
    private_key: string;
  };
  if (!credentials.client_email || !credentials.private_key) {
    throw new Error('GDRIVE_SERVICE_ACCOUNT_JSON is missing client_email or private_key');
  }

  const auth = new google.auth.JWT({
    email: credentials.client_email,
    key: credentials.private_key,
    scopes: ['https://www.googleapis.com/auth/drive'],
  });
  const drive = google.drive({ version: 'v3', auth });
  return new GoogleApiDriveClient(drive);
}

class GoogleApiDriveClient implements DriveClient {
  constructor(private readonly drive: drive_v3.Drive) {}

  async findFolder(name: string, parentId: string): Promise<string | undefined> {
    const result = await this.drive.files.list({
      q: `'${escapeQueryValue(parentId)}' in parents and name='${escapeQueryValue(name)}' and mimeType='application/vnd.google-apps.folder' and trashed=false`,
      fields: 'files(id,name)',
      pageSize: 10,
      supportsAllDrives: true,
      includeItemsFromAllDrives: true,
    });
    return result.data.files?.[0]?.id ?? undefined;
  }

  async createFolder(name: string, parentId: string): Promise<string> {
    const result = await this.drive.files.create({
      requestBody: {
        name,
        mimeType: 'application/vnd.google-apps.folder',
        parents: [parentId],
      },
      fields: 'id',
      supportsAllDrives: true,
    });
    if (!result.data.id) throw new Error(`Drive did not return an id for folder ${name}`);
    return result.data.id;
  }

  async uploadFile(input: {
    name: string;
    parentId: string;
    mimeType: string;
    body: Buffer;
  }): Promise<string> {
    const result = await this.drive.files.create({
      requestBody: {
        name: input.name,
        parents: [input.parentId],
      },
      media: {
        mimeType: input.mimeType,
        body: Readable.from(input.body),
      },
      fields: 'id',
      supportsAllDrives: true,
    });
    if (!result.data.id) throw new Error(`Drive did not return an id for file ${input.name}`);
    return result.data.id;
  }
}

async function ensureFolder(client: DriveClient, parentId: string, name: string): Promise<string> {
  return (await client.findFolder(name, parentId)) ?? client.createFolder(name, parentId);
}

function mimeTypeFor(fileName: string): string {
  switch (extname(fileName).toLowerCase()) {
    case '.json':
      return 'application/json';
    case '.txt':
      return 'text/plain';
    case '.htm':
    case '.html':
      return 'text/html';
    case '.pdf':
      return 'application/pdf';
    default:
      return 'application/octet-stream';
  }
}

async function uploadLocalFile(
  client: DriveClient,
  localPath: string,
  parentId: string,
): Promise<void> {
  await client.uploadFile({
    name: basename(localPath),
    parentId,
    mimeType: mimeTypeFor(localPath),
    body: await readFile(localPath),
  });
}

export async function uploadRunToDrive(input: {
  client: DriveClient;
  rootFolderId: string;
  date: string;
  runDir: string;
}): Promise<DriveUploadSummary> {
  const runsFolderId = await ensureFolder(input.client, input.rootFolderId, 'runs');
  const dateFolderId = await ensureFolder(input.client, runsFolderId, input.date);
  const sourcesFolderId = await ensureFolder(input.client, dateFolderId, 'sources');
  const rawFolderId = await ensureFolder(input.client, sourcesFolderId, 'raw');
  const logsFolderId = await ensureFolder(input.client, dateFolderId, 'logs');

  let uploadedFiles = 0;
  for (const fileName of ['discovery-manifest.json', 'fetch-manifest.json']) {
    await uploadLocalFile(input.client, join(input.runDir, fileName), sourcesFolderId);
    uploadedFiles += 1;
  }

  await uploadLocalFile(input.client, join(input.runDir, 'fetch-log.txt'), logsFolderId);
  uploadedFiles += 1;

  const rawLocalDir = join(input.runDir, 'raw');
  for (const fileName of (await readdir(rawLocalDir)).sort()) {
    await uploadLocalFile(input.client, join(rawLocalDir, fileName), rawFolderId);
    uploadedFiles += 1;
  }

  return {
    uploadedFiles,
    dateFolderId,
    sourcesFolderId,
    rawFolderId,
    logsFolderId,
  };
}
