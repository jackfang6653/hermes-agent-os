// SPDX-License-Identifier: MIT

export interface Brand {
  id: string;
  name: string;
  slug: string;
  category: 'furniture' | 'lighting' | 'home_decor' | 'textile';
  style: string[];
  positioning: string[];
  dna: BrandDNA;
  createdAt: string;
  updatedAt: string;
}

export interface BrandDNA {
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
