// SPDX-License-Identifier: MIT

import type { DNASchema, BrandProfile } from './types';

export function extractDNA(profile: Partial<BrandProfile>): DNASchema {
  return {
    visual: {
      style: profile.style?.[0] ?? 'nordic',
      atmosphere: profile.positioning ?? ['calm', 'warm', 'refined'],
      colorPalette: profile.dna?.visual?.colorPalette ?? ['#f5f0e8', '#d4c5b0', '#8b7355'],
    },
    preserve: {
      productGeometry: true,
      materialTexture: true,
      colorAccuracy: true,
    },
    variable: {
      camera: true,
      scene: true,
      composition: true,
    },
  };
}

export function validateDNARules(dna: DNASchema, data: Record<string, unknown>): string[] {
  const violations: string[] = [];

  if (dna.preserve.productGeometry && data.geometryChanged === true) {
    violations.push('Product geometry must be preserved');
  }
  if (dna.preserve.materialTexture && data.textureChanged === true) {
    violations.push('Material texture must be preserved');
  }
  if (dna.preserve.colorAccuracy && data.colorShifted === true) {
    violations.push('Color accuracy must be maintained');
  }

  return violations;
}
