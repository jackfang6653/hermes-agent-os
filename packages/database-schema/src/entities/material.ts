// SPDX-License-Identifier: MIT

export interface Material {
  id: string;
  name: string;
  type: MaterialType;
  category: 'wood' | 'fabric' | 'metal' | 'stone' | 'leather' | 'glass' | 'ceramic' | 'composite';
  properties: MaterialProperties;
  careInstructions: string[];
  sustainability: SustainabilityInfo;
}

export type MaterialType = 'solid_wood' | 'veneer' | 'linen' | 'cotton' | 'polyester' | 'wool' |
  'stainless_steel' | 'brass' | 'aluminum' | 'iron' | 'marble' | 'granite' | 'quartz' |
  'full_grain_leather' | 'top_grain_leather' | 'pu_leather' | 'tempered_glass' | 'ceramic' | 'resin';

export interface MaterialProperties {
  durability: 1 | 2 | 3 | 4 | 5;
  waterResistance: 1 | 2 | 3 | 4 | 5;
  stainResistance: 1 | 2 | 3 | 4 | 5;
  uvResistance: 1 | 2 | 3 | 4 | 5;
  texture: 'smooth' | 'rough' | 'woven' | 'grain' | 'polished' | 'matte';
  weight: 'light' | 'medium' | 'heavy';
}

export interface SustainabilityInfo {
  renewable: boolean;
  recyclable: boolean;
  certifications: string[];
  carbonFootprint?: number;
}
