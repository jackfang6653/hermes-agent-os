// SPDX-License-Identifier: MIT
import { describe, it, expect } from 'vitest';
import { BrandEngine } from '../src/engine.js';
import { distillDNA } from '../src/dna.js';
import { createNORHORGrammar, validateLighting, validateColor } from '../src/grammar.js';
import type { BrandProfile } from '../src/types.js';

describe('BrandEngine', () => {
  it('should create NORHOR engine with defaults', () => {
    const engine = BrandEngine.createNORHOREngine();
    const profile = engine.get('norhor');
    expect(profile).toBeDefined();
    expect(profile!.name).toBe('NORHOR');
    expect(profile!.style).toContain('nordic');
  });

  it('should analyze and extract DNA', () => {
    const engine = new BrandEngine();
    const dna = engine.analyze({ style: ['japanese'], positioning: ['wabi_sabi'] });
    expect(dna.visual.style).toBe('japanese');
    expect(dna.preserve.productGeometry).toBe(true);
  });

  it('should validate content against brand', () => {
    const engine = BrandEngine.createNORHOREngine();
    const result = engine.validate('norhor', { style: 'industrial', color: '#ff0000', geometryChanged: true });
    expect(result.score).toBeLessThan(1);
    expect(result.errors.length).toBeGreaterThan(0);
  });

  it('should pass validation for brand-compliant content', () => {
    const engine = BrandEngine.createNORHOREngine();
    const result = engine.validate('norhor', { style: 'nordic', lighting: 'natural_side_lighting' });
    expect(result.valid).toBe(true);
  });

  it('should suggest brand parameters', () => {
    const engine = BrandEngine.createNORHOREngine();
    const suggestion = engine.suggest('norhor');
    expect(suggestion.lighting).toBeDefined();
    expect((suggestion.colorPalette as string[]).length).toBeGreaterThan(0);
  });
});

describe('DNA extraction', () => {
  it('should extract from partial profile', () => {
    const dna = distillDNA({});
    expect(dna.visual.style).toBe('nordic');
    expect(dna.preserve.productGeometry).toBe(true);
  });
});

describe('Grammar', () => {
  it('should validate lighting rules', () => {
    const grammar = createNORHORGrammar();
    expect(validateLighting('natural', grammar)).toBe(true);
    expect(validateLighting('fluorescent', grammar)).toBe(false);
  });

  it('should classify colors', () => {
    const grammar = createNORHORGrammar();
    expect(validateColor('#f5f0e8', grammar)).toBe('brand');
    expect(validateColor('#ff0000', grammar)).toBe('avoid');
    expect(validateColor('#00ff00', grammar)).toBe('avoid');
    expect(validateColor('#808080', grammar)).toBe('neutral');
  });
});
