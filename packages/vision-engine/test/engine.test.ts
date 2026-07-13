// SPDX-License-Identifier: MIT
import { describe, it, expect } from 'vitest';
import { VisionEngine } from '../src/engine';
import { ProductAnalyzer } from '../src/analyzers/product-analyzer';
import { ColorAnalyzer } from '../src/analyzers/color-analyzer';

describe('VisionEngine', () => {
  it('should create engine', () => {
    const engine = new VisionEngine();
    expect(engine).toBeInstanceOf(VisionEngine);
  });

  it('should analyze product type', async () => {
    const engine = new VisionEngine();
    const result = await engine.analyze('https://example.com/img.jpg', 'product');
    expect(result.type).toBe('product');
    expect(result.confidence).toBeGreaterThan(0);
  });

  it('should analyze color', async () => {
    const engine = new VisionEngine();
    const result = await engine.analyze('https://example.com/img.jpg', 'color');
    expect(result.type).toBe('color');
    expect(result.data.dominantColor).toBeTruthy();
  });

  it('should analyze all types', async () => {
    const engine = new VisionEngine();
    const results = await engine.analyzeAll('https://example.com/img.jpg');
    expect(results.size).toBeGreaterThan(0);
  });

  it('should throw for unknown type', async () => {
    const engine = new VisionEngine();
    await expect(engine.analyze('test.jpg', 'layout' as any)).rejects.toThrow();
  });
});

describe('ProductAnalyzer', () => {
  it('should create analyzer', () => {
    const a = new ProductAnalyzer({});
    expect(a).toBeInstanceOf(ProductAnalyzer);
  });
});

describe('ColorAnalyzer', () => {
  it('should return color data', async () => {
    const a = new ColorAnalyzer({});
    const result = await a.analyze('test.jpg');
    expect(result.data.dominantColor).toBe('#f5f0e8');
    expect(result.data.palette).toHaveLength(4);
  });
});
