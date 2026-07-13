// SPDX-License-Identifier: MIT

export { BrandEngine } from './engine';
export { extractDNA, validateDNARules } from './dna';
export { createNORHORGrammar, validateLighting, validateColor } from './grammar';
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
