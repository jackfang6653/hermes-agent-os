// SPDX-License-Identifier: MIT
import { describe, it, expect } from 'vitest';
import { createDefaultConfig, mergeConfig } from '../src/config';
import { ROUTES, SIDEBAR_ROUTES, findRoute } from '../src/routes';

describe('Desktop Config', () => {
  it('should create default config', () => {
    const config = createDefaultConfig();
    expect(config.window.width).toBe(1280);
    expect(config.theme.mode).toBe('dark');
    expect(config.editor.autoSave).toBe(true);
  });

  it('should merge partial config', () => {
    const defaults = createDefaultConfig();
    const merged = mergeConfig(defaults, { theme: { mode: 'light' } as any });
    expect(merged.theme.mode).toBe('light');
    expect(merged.window.width).toBe(1280); // unchanged
  });
});

describe('Routes', () => {
  it('should have 8 routes total', () => {
    expect(ROUTES).toHaveLength(8);
  });

  it('sidebar should exclude detail routes', () => {
    expect(SIDEBAR_ROUTES.length).toBeLessThan(ROUTES.length);
  });

  it('should find route by pattern', () => {
    const route = findRoute('/projects/abc123');
    expect(route?.name).toBe('Project Detail');
  });

  it('should return undefined for unknown routes', () => {
    expect(findRoute('/unknown')).toBeUndefined();
  });
});
