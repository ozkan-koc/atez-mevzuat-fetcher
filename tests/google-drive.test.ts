import { mkdtemp, mkdir, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { uploadRunToDrive, type DriveClient } from '../src/google-drive.js';

class FakeDrive implements DriveClient {
  folders = new Map<string, string>();
  uploads: Array<{ name: string; parentId: string; mimeType: string }> = [];
  nextId = 1;

  async findFolder(name: string, parentId: string): Promise<string | undefined> {
    return this.folders.get(`${parentId}/${name}`);
  }

  async createFolder(name: string, parentId: string): Promise<string> {
    const id = `folder-${this.nextId++}`;
    this.folders.set(`${parentId}/${name}`, id);
    return id;
  }

  async uploadFile(input: { name: string; parentId: string; mimeType: string; body: Buffer }): Promise<string> {
    this.uploads.push({ name: input.name, parentId: input.parentId, mimeType: input.mimeType });
    return `file-${this.nextId++}`;
  }
}

describe('Google Drive upload', () => {
  it('creates the canonical run folders and routes source/raw/log files correctly', async () => {
    const runDir = await mkdtemp(join(tmpdir(), 'atez-drive-'));
    await mkdir(join(runDir, 'raw'));
    await writeFile(join(runDir, 'discovery-manifest.json'), '{}');
    await writeFile(join(runDir, 'fetch-manifest.json'), '{}');
    await writeFile(join(runDir, 'fetch-log.txt'), 'log');
    await writeFile(join(runDir, 'raw', '20260818-1.htm'), '<html/>');
    await writeFile(join(runDir, 'raw', '20260818-2.pdf'), Buffer.from('%PDF'));

    const client = new FakeDrive();
    const summary = await uploadRunToDrive({
      client,
      rootFolderId: 'root-id',
      date: '2026-08-18',
      runDir,
    });

    expect(summary.uploadedFiles).toBe(5);
    expect(client.folders.has('root-id/runs')).toBe(true);
    const runsId = client.folders.get('root-id/runs')!;
    expect(client.folders.has(`${runsId}/2026-08-18`)).toBe(true);
    expect(client.uploads.map((u) => u.name).sort()).toEqual([
      '20260818-1.htm',
      '20260818-2.pdf',
      'discovery-manifest.json',
      'fetch-log.txt',
      'fetch-manifest.json',
    ]);
    expect(client.uploads.find((u) => u.name.endsWith('.pdf'))?.mimeType).toBe('application/pdf');
  });
});
