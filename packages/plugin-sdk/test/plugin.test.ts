// SPDX-License-Identifier: MIT
import { describe, it, expect } from 'vitest';
import { PluginLoader } from '../src/loader.js';
import { PluginMarketplace, BUILTIN_PLUGINS } from '../src/marketplace.js';
import type { PluginManifest } from '../src/types.js';

const testManifest: PluginManifest = {
  id: 'test-plugin',
  name: 'Test Plugin',
  version: '1.0.0',
  description: 'A test plugin',
  author: 'Test',
  license: 'MIT',
  entry: 'index.js',
  dependencies: [],
  capabilities: ['analyze'],
  hooks: ['onBeforeGenerate'],
  permissions: ['path:/tmp'],
};

describe('PluginLoader', () => {
  it('should load a plugin', async () => {
    const loader = new PluginLoader();
    const ctx = await loader.load(testManifest);
    expect(ctx.manifest.id).toBe('test-plugin');
    expect(loader.count()).toBe(1);
  });

  it('should reject duplicate load', async () => {
    const loader = new PluginLoader();
    await loader.load(testManifest);
    await expect(loader.load(testManifest)).rejects.toThrow();
  });

  it('should unload plugins', async () => {
    const loader = new PluginLoader();
    await loader.load(testManifest);
    expect(loader.unload('test-plugin')).toBe(true);
    expect(loader.count()).toBe(0);
  });

  it('should list loaded plugins', async () => {
    const loader = new PluginLoader();
    await loader.load(testManifest);
    expect(loader.list()).toHaveLength(1);
  });

  it('should provide storage API', async () => {
    const loader = new PluginLoader();
    const ctx = await loader.load(testManifest);
    await ctx.api.storage.set('key', 'value');
    const val = await ctx.api.storage.get('key');
    expect(val).toBe('value');
  });
});

describe('PluginMarketplace', () => {
  it('should have builtin plugins', () => {
    expect(BUILTIN_PLUGINS.length).toBeGreaterThan(0);
  });

  it('should search plugins', () => {
    const m = new PluginMarketplace();
    const results = m.search('NORHOR');
    expect(results.length).toBeGreaterThan(0);
  });

  it('should filter by source', () => {
    const m = new PluginMarketplace();
    const builtins = m.listBySource('builtin');
    expect(builtins.length).toBeGreaterThan(0);
  });
});
