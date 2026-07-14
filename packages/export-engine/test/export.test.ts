// SPDX-License-Identifier: MIT
import { describe, it, expect } from 'vitest';
import { ExportEngine } from '../src/engine';
import { FORMATTERS, getFormatter, validateOptions } from '../src/exporters';
import type { ExportRequest } from '../src/types';

describe('ExportEngine', () => {
  const request: ExportRequest = {
    projectId: 'proj-1',
    products: ['p1', 'p2', 'p3'],
    format: 'html',
    options: { quality: 'standard', includeMetadata: true, imageResolution: '1080p', watermark: false, compression: true },
  };

  it('should export successfully', async () => {
    const engine = new ExportEngine();
    const htmlRequest: ExportRequest = {
      projectId: 'proj-1', products: ['p1', 'p2', 'p3'],
      format: 'html',
      options: { quality: 'standard', includeMetadata: true, imageResolution: '720p', watermark: false, compression: false },
    };
    const result = await engine.export(htmlRequest);
    expect(result.status).toBe('completed');
    expect(result.format).toBe('html');
  });

  it('should fail on unknown format', async () => {
    const engine = new ExportEngine();
    const result = await engine.export({ ...request, format: 'unknown' as any });
    expect(result.status).toBe('failed');
  });

  it('should track history', async () => {
    const engine = new ExportEngine();
    await engine.export({ ...request, options: { quality: 'standard', includeMetadata: true, imageResolution: '720p', watermark: false, compression: false } });
    await engine.export({ ...request, format: 'json', options: { quality: 'standard', includeMetadata: true, imageResolution: '720p', watermark: false, compression: false } });
    expect(engine.getHistory()).toHaveLength(2);
  });

  it('should get recent exports', async () => {
    const engine = new ExportEngine();
    for (let i = 0; i < 5; i++) {
      await engine.export({ ...request, projectId: `proj-${i}`, options: { quality: 'standard', includeMetadata: true, imageResolution: '720p', watermark: false, compression: false } });
    }
    const recent = engine.getRecent(3);
    expect(recent).toHaveLength(3);
  });

  it('should register and retrieve templates', () => {
    const engine = new ExportEngine();
    engine.registerTemplate('norhor-detail', '<html>{{content}}</html>');
    expect(engine.getTemplate('norhor-detail')).toBe('<html>{{content}}</html>');
  });
});

describe('Exporters', () => {
  it('should have 5 formatters', () => {
    expect(FORMATTERS).toHaveLength(5);
  });

  it('should find formatter by format', () => {
    const f = getFormatter('html');
    expect(f?.name).toBe('Responsive HTML');
  });

  it('should return undefined for unknown', () => {
    expect(getFormatter('xyz')).toBeUndefined();
  });

  it('should validate options', () => {
    const errors = validateOptions('html', { includeMetadata: true, watermark: false } as any);
    expect(errors).toHaveLength(0); // unsupported options are silently ignored
  });
});
