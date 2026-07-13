// SPDX-License-Identifier: MIT

import type { BrandProfile, DNASchema, ValidationResult, Constraint, ConstraintViolation } from './types';
import { extractDNA, validateDNARules } from './dna';
import { createNORHORGrammar, validateLighting, validateColor } from './grammar';

export class BrandEngine {
  private profiles: Map<string, BrandProfile> = new Map();

  register(profile: BrandProfile): void {
    this.profiles.set(profile.id, profile);
  }

  get(id: string): BrandProfile | undefined {
    return this.profiles.get(id);
  }

  analyze(profile: Partial<BrandProfile>): DNASchema {
    return extractDNA(profile);
  }

  validate(profileId: string, data: Record<string, unknown>): ValidationResult {
    const profile = this.profiles.get(profileId);
    if (!profile) {
      return { valid: false, errors: [{ constraint: 'missing_profile', field: 'id', message: 'Profile not found' }], warnings: [], score: 0 };
    }

    const errors: ConstraintViolation[] = [];
    const warnings: ConstraintViolation[] = [];

    // DNA preservation check
    const dnaViolations = validateDNARules(profile.dna, data);
    for (const v of dnaViolations) {
      errors.push({ constraint: 'dna_preserve', field: 'dna', message: v });
    }

    // Grammar validation
    const grammar = profile.grammar;
    if (data.lighting && !validateLighting(String(data.lighting), grammar)) {
      warnings.push({ constraint: 'lighting', field: 'lighting', message: `Lighting '${data.lighting}' not in brand grammar` });
    }

    if (data.color && grammar.color.avoidColors.includes(String(data.color))) {
      errors.push({ constraint: 'color', field: 'color', message: `Color '${data.color}' is in avoid list` });
    }

    // Custom constraints
    for (const c of profile.constraints) {
      if (data[c.field] !== undefined) {
        const matched = String(data[c.field]).match(new RegExp(c.rule));
        if (!matched) {
          const v: ConstraintViolation = { constraint: c.field, field: c.field, message: c.message };
          if (c.severity === 'error') errors.push(v);
          else warnings.push(v);
        }
      }
    }

    const score = errors.length === 0 ? 1 : Math.max(0, 1 - errors.length * 0.25);
    return { valid: errors.length === 0, errors, warnings, score };
  }

  suggest(profileId: string): Record<string, unknown> {
    const profile = this.profiles.get(profileId);
    if (!profile) return {};

    return {
      lighting: profile.grammar.lighting.default,
      colorPalette: profile.grammar.color.brandPalette,
      composition: profile.grammar.composition.style,
      atmosphere: profile.dna.visual.atmosphere,
    };
  }

  static createNORHOREngine(): BrandEngine {
    const engine = new BrandEngine();
    engine.register({
      id: 'norhor',
      name: 'NORHOR',
      slug: 'norhor',
      style: ['nordic', 'minimal', 'modern'],
      positioning: ['calm', 'warm', 'refined'],
      dna: {
        visual: { style: 'nordic', atmosphere: ['calm', 'warm', 'refined'], colorPalette: ['#f5f0e8', '#d4c5b0', '#8b7355'] },
        preserve: { productGeometry: true, materialTexture: true, colorAccuracy: true },
        variable: { camera: true, scene: true, composition: true },
      },
      grammar: createNORHORGrammar(),
      constraints: [
        { field: 'style', rule: 'nordic|minimal|modern|scandinavian', severity: 'error', message: 'Style must match NORHOR brand identity' },
        { field: 'atmosphere', rule: 'calm|warm|refined|natural|cozy', severity: 'warn', message: 'Consider NORHOR brand atmosphere' },
      ],
    });
    return engine;
  }
}
