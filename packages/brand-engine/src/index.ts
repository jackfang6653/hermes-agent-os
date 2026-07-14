// SPDX-License-Identifier: MIT

export { BrandEngine } from './engine.js';
export { distillDNA, evaluateBrandFit } from './dna.js';
export { createNORHORGrammar, validateLighting, validateColor } from './grammar.js';
export type {
  BrandProfile,
  DNASchema,
  VisualGrammar,
  LightingRule,
  CompositionRule,
  ColorRule,
  Constraint,
  ValidationResult,
  ConstraintViolation,
} from './types';
export const VERSION = '1.0.0';
