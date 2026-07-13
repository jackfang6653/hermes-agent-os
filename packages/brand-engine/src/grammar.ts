// SPDX-License-Identifier: MIT

import type { VisualGrammar, LightingRule, CompositionRule, ColorRule } from './types';

export const DEFAULT_LIGHTING: LightingRule = {
  preferred: ['natural', 'soft_diffuse', 'warm_ambient'],
  avoid: ['harsh_direct', 'fluorescent', 'colored_gel'],
  default: 'natural_side_lighting',
  temperature: [3500, 5500],
};

export const DEFAULT_COMPOSITION: CompositionRule = {
  style: 'minimal_centered',
  productPosition: 'center',
  whitespace: 'ample',
  aspectRatio: '4:3',
};

export const DEFAULT_COLORS: ColorRule = {
  brandPalette: ['#f5f0e8', '#d4c5b0', '#8b7355', '#2c2c2c'],
  accentColors: ['#c4a882', '#e8d5c4'],
  avoidColors: ['#ff0000', '#00ff00', '#0000ff'],
  saturation: [0.1, 0.4],
};

export function createNORHORGrammar(): VisualGrammar {
  return {
    lighting: DEFAULT_LIGHTING,
    composition: DEFAULT_COMPOSITION,
    color: DEFAULT_COLORS,
  };
}

export function validateLighting(lightingType: string, grammar: VisualGrammar): boolean {
  return !grammar.lighting.avoid.includes(lightingType);
}

export function validateColor(hex: string, grammar: VisualGrammar): 'brand' | 'accent' | 'avoid' | 'neutral' {
  if (grammar.color.brandPalette.includes(hex)) return 'brand';
  if (grammar.color.accentColors.includes(hex)) return 'accent';
  if (grammar.color.avoidColors.includes(hex)) return 'avoid';
  return 'neutral';
}
