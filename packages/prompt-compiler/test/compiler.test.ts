// SPDX-License-Identifier: MIT
import { describe, it, expect } from 'vitest';
import { PromptCompiler } from '../src/compiler.js';
import { PRODUCT_PROMPT, SCENE_PROMPT, DETAIL_PROMPT } from '../src/templates/prompts.js';
import { validatePrompt, sanitizePrompt } from '../src/validators.js';

describe('PromptCompiler', () => {
  it('should compile a template with variables', () => {
    const compiler = new PromptCompiler();
    compiler.register(PRODUCT_PROMPT);
    const result = compiler.compile('product-main', {
      style: 'nordic',
      product_type: 'sofa',
      material: 'linen',
      color: 'beige',
    });
    expect(result.prompt).toContain('nordic');
    expect(result.prompt).toContain('sofa');
    expect(result.prompt).toContain('linen');
    expect(result.metadata.warnings).toHaveLength(0);
  });

  it('should apply default values for missing variables', () => {
    const compiler = new PromptCompiler();
    compiler.register(PRODUCT_PROMPT);
    const result = compiler.compile('product-main', {
      style: 'nordic',
      product_type: 'chair',
      material: 'wood',
      color: 'natural',
    });
    expect(result.prompt).toContain('natural'); // lighting default
    expect(result.prompt).toContain('8K');       // resolution default
  });

  it('should throw on missing required variable in strict mode', () => {
    const compiler = new PromptCompiler();
    compiler.register(PRODUCT_PROMPT);
    expect(() => compiler.compile('product-main', {
      style: 'nordic',
      product_type: 'table',
      material: 'wood',
      // missing: color
    } as any)).toThrow();
  });

  it('should register scene and detail templates', () => {
    const compiler = new PromptCompiler();
    compiler.register(SCENE_PROMPT);
    compiler.register(DETAIL_PROMPT);
    expect(compiler.getTemplate('scene-lifestyle')).toBeDefined();
    expect(compiler.getTemplate('detail-story')).toBeDefined();
  });

  it('should compile scene template', () => {
    const compiler = new PromptCompiler();
    compiler.register(SCENE_PROMPT);
    const result = compiler.compile('scene-lifestyle', {
      scene_style: 'nordic',
      room_type: 'living room',
      product_type: 'sofa',
      product_color: 'beige',
      color_palette: 'warm neutrals',
    });
    expect(result.prompt).toContain('nordic');
    expect(result.prompt).toContain('living room');
  });
});

describe('Simple compile', () => {
  it('should do simple string interpolation', () => {
    const result = PromptCompiler.simpleCompile('Hello {{name}}!', { name: 'World' });
    expect(result).toBe('Hello World!');
  });
});

describe('Validators', () => {
  it('should validate prompt length', () => {
    const warnings = validatePrompt('short', 100);
    expect(warnings).toHaveLength(0);

    const long = validatePrompt('x'.repeat(200), 100);
    expect(long.length).toBeGreaterThan(0);
  });

  it('should sanitize prompts', () => {
    const result = sanitizePrompt('hello   world..  test,,' );
    expect(result).toBe('hello world. test,');
  });
});
