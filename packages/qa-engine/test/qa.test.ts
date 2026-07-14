// SPDX-License-Identifier: MIT
import { describe, it, expect } from 'vitest';
import { QAEngine } from '../src/engine';
import { DEFAULT_RULES, DEFAULT_CONFIG } from '../src/rules';
import type { QAReport } from '../src/types';

describe('QAEngine', () => {
  it('should create with default config', () => {
    const engine = new QAEngine();
    expect(engine.getConfig().minScore).toBe(0.7);
    expect(engine.getConfig().rules.length).toBeGreaterThan(0);
  });

  it('should run brand compliance check', async () => {
    const engine = new QAEngine();
    const report = await engine.runCheck('brand_compliance', 'prod-1', 'product', {
      brand_style: true,
      brand_colors: true,
      brand_lighting: false,
    });
    expect(report.type).toBe('brand_compliance');
    expect(report.checks.length).toBeGreaterThan(0);
  });

  it('should run image quality check', async () => {
    const engine = new QAEngine();
    const report = await engine.runCheck('image_quality', 'img-1', 'image', {
      img_resolution: true,
      img_format: false,
      img_blur: true,
    });
    expect(report.targetId).toBe('img-1');
  });

  it('should pass when all checks pass', async () => {
    const engine = new QAEngine();
    const report = await engine.runCheck('brand_compliance', 'ok', 'product', {
      brand_style: true,
      brand_colors: true,
      brand_lighting: true,
    });
    expect(report.passed).toBe(true);
  });

  it('should fail when score below threshold', async () => {
    const engine = new QAEngine({ minScore: 0.7 });
    const report = await engine.runCheck('brand_compliance', 'bad', 'product', {
      brand_style: false,
      brand_colors: false,
    });
    expect(report.passed).toBe(false);
  });

  it('should check brand compliance', async () => {
    const engine = new QAEngine();
    const check = await engine.checkBrandCompliance({ style: 'nordic', lighting: 'natural' });
    expect(check.styleMatch).toBe(true);
    expect(check.lightingValid).toBe(true);
  });

  it('should check image quality', async () => {
    const engine = new QAEngine();
    const check = await engine.checkImageQuality({ width: 2048, height: 2048, format: 'png' });
    expect(check.resolution.width).toBe(2048);
  });
});

describe('Default Rules', () => {
  it('should have 10 rules', () => {
    expect(DEFAULT_RULES).toHaveLength(10);
  });

  it('should cover all categories', () => {
    const categories = new Set(DEFAULT_RULES.map(r => r.category));
    expect(categories.size).toBe(4);
  });
});
