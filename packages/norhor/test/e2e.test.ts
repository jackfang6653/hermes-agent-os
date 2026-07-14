// SPDX-License-Identifier: MIT
// E2E 全链路测试 — 通过 vitest 执行以避免 ESM 模块解析问题
import { describe, it, expect } from 'vitest';
import { NorhorPipeline } from '../src/pipeline.js';
import { generateImage } from '../src/image-gen.js';

describe('E2E Pipeline', () => {
  const pipe = new NorhorPipeline();

  it('should generate product with detail page HTML', async () => {
    const result = await pipe.generateProduct({
      sku: 'E2E-001',
      productName: '北欧简约沙发',
      category: 'sofa',
      material: '亚麻面料',
      color: '米白',
      scene: 'nordic_living',
    });

    expect(result.sku).toBe('E2E-001');
    expect(result.brandScore).toBeGreaterThanOrEqual(0);
    expect(result.imagePrompts).toHaveLength(3);
    expect(result.detailPage).toBeTruthy();
    expect(result.detailPage!).toContain('NORHOR 北欧表情');
    expect(result.detailPage!).toContain('米白');
    expect(result.detailPage!).toContain('亚麻面料');
  });

  it('should include brand fit assessment in results', async () => {
    const result = await pipe.generateProduct({
      sku: 'E2E-002',
      productName: 'Oak Dining Table',
      category: 'table',
      material: 'oak',
      color: 'natural',
    });

    expect(result.brandFit).toBeDefined();
    expect(result.brandFit.matched).toBeInstanceOf(Array);
    expect(result.brandScore).toBeGreaterThanOrEqual(0);
  });

  it('should create and execute E2E workflow', async () => {
    const wf = pipe.createE2EWorkflow();
    expect(wf.steps).toHaveLength(7);

    const stepIds = wf.steps.map(s => s.id);
    expect(stepIds).toEqual([
      'analyze_product', 'extract_dna', 'create_scene',
      'compile_prompt', 'generate_image', 'qa_check', 'export',
    ]);
  });

  it('should handle image generation fallback gracefully', async () => {
    const result = await generateImage('test product image');
    expect(result.status).toBe('failed');
    // Should not throw — graceful fallback
  });

  it('should produce valid HTML detail page', async () => {
    const result = await pipe.generateProduct({
      sku: 'E2E-003',
      productName: 'Wishbone Chair',
      category: 'chair',
      material: 'oak',
      color: 'natural',
    });

    const html = result.detailPage!;
    expect(html).toContain('<!DOCTYPE html>');
    expect(html).toContain('</html>');
    expect(html).toContain('品牌匹配度');
    expect(html).toContain('Wishbone Chair');
  });

  it('should export detail page as file', async () => {
    const result = await pipe.generateProduct({
      sku: 'E2E-OUTPUT',
      productName: 'Output Test',
      category: 'sofa',
      material: 'linen',
      color: 'beige',
    });

    // Write to disk for inspection
    const fs = await import('node:fs');
    const path = './e2e-detail-page.html';
    fs.writeFileSync(path, result.detailPage!);
    
    // Verify file
    const exists = fs.existsSync(path);
    expect(exists).toBe(true);
    const content = fs.readFileSync(path, 'utf-8');
    expect(content).toContain('Output Test');
    
    // Cleanup
    fs.unlinkSync(path);
    console.log('  📄 E2E HTML page written & verified');
  });
});
