// SPDX-License-Identifier: MIT

export interface BrandProfile {
  id: string;
  name: string;
  slug: string;
  style: string[];
  positioning: string[];
  dna: DNASchema;
  grammar: VisualGrammar;
  constraints: Constraint[];
}

export interface DNASchema {
  visual: {
    style: string;
    atmosphere: string[];
    colorPalette: string[];
  };
  preserve: {
    productGeometry: boolean;
    materialTexture: boolean;
    colorAccuracy: boolean;
  };
  variable: {
    camera: boolean;
    scene: boolean;
    composition: boolean;
  };
}

export interface VisualGrammar {
  lighting: LightingRule;
  composition: CompositionRule;
  color: ColorRule;
}

export interface LightingRule {
  preferred: string[];
  avoid: string[];
  default: string;
  temperature: [number, number];
}

export interface CompositionRule {
  style: string;
  productPosition: string;
  whitespace: string;
  aspectRatio: string;
}

export interface ColorRule {
  brandPalette: string[];
  accentColors: string[];
  avoidColors: string[];
  saturation: [number, number];
}

export interface Constraint {
  field: string;
  rule: string;
  severity: 'error' | 'warn' | 'info';
  message: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: ConstraintViolation[];
  warnings: ConstraintViolation[];
  score: number;
}

export interface ConstraintViolation {
  constraint: string;
  field: string;
  message: string;
}
