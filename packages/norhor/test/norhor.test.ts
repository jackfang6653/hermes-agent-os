// SPDX-License-Identifier: MIT
import { describe, it, expect } from 'vitest';
import { NorhorPipeline } from '../src/pipeline.js';
import { NORHOR_PROFILE, SCENE_PRESETS, PRODUCT_CATEGORIES } from '../src/presets.js';

describe('NORHOR Pipeline', () => {
  const pipeline = new NorhorPipeline();

  it('should generate product prompts', async () => {
    const result = await pipeline.generateProduct({
      sku: 'CS-001',
      productName: 'Cloud Sofa',
      category: 'sofa',
      material: 'linen',
      color: 'beige',
      scene: 'nordic_living',
    });

    expect(result.sku).toBe('CS-001');
    expect(result.imagePrompts).toHaveLength(3);
    expect(result.brandScore).toBeGreaterThanOrEqual(0);
  });

  it('should include product main prompt', async () => {
    const result = await pipeline.generateProduct({
      sku: 'WC-001',
      productName: 'Wishbone Chair',
      category: 'chair',
      material: 'oak',
      color: 'natural',
    });

    const productPrompt = result.imagePrompts.find(p => p.type === 'product_main');
    expect(productPrompt).toBeDefined();
    expect(productPrompt!.prompt).toContain('oak');
    expect(productPrompt!.prompt).toContain('chair');
  });

  it('should include scene prompt', async () => {
    const result = await pipeline.generateProduct({
      sku: 'TB-001',
      productName: 'Oak Table',
      category: 'table',
      material: 'oak',
      color: 'natural',
      scene: 'modern_dining',
    });

    const scenePrompt = result.imagePrompts.find(p => p.type === 'scene_lifestyle');
    expect(scenePrompt).toBeDefined();
    expect(scenePrompt!.prompt).toContain('Oak Table');
  });

  it('should validate brand compliance', () => {
    const valid = pipeline.validateBrand('nordic', '#f5f0e8', 'natural');
    expect(valid.valid).toBe(true);

    const invalid = pipeline.validateBrand('industrial', '#ff0000', 'fluorescent');
    expect(invalid.valid).toBe(false);
  });
});

describe('NORHOR Presets', () => {
  it('should have brand profile', () => {
    expect(NORHOR_PROFILE.name).toBe('NORHOR');
    expect(NORHOR_PROFILE.style).toContain('nordic');
  });

  it('should have scene presets', () => {
    expect(Object.keys(SCENE_PRESETS)).toHaveLength(3);
    expect(SCENE_PRESETS.nordic_living.moodKeywords).toContain('calm');
  });

  it('should have product categories', () => {
    expect(PRODUCT_CATEGORIES.length).toBeGreaterThanOrEqual(6);
    const sofa = PRODUCT_CATEGORIES.find(c => c.id === 'sofa');
    expect(sofa?.scenes).toContain('nordic_living');
  });
});
