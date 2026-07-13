// SPDX-License-Identifier: MIT

export interface Product {
  id: string;
  sku: string;
  name: string;
  brandId: string;
  categoryId: string;
  subcategoryId?: string;
  description: string;
  dimensions: Dimensions;
  materials: MaterialInfo[];
  color: ColorInfo;
  texture: string;
  craftsmanship: string;
  images: ProductImage[];
  fixedParameters: Record<string, unknown>;
  variableParameters: Record<string, unknown>;
  tags: string[];
  status: 'active' | 'draft' | 'archived';
  createdAt: string;
  updatedAt: string;
}

export interface Dimensions {
  width: number;
  height: number;
  depth: number;
  unit: 'cm' | 'mm' | 'inch';
}

export interface MaterialInfo {
  name: string;
  type: string;
  percentage?: number;
  description?: string;
}

export interface ColorInfo {
  name: string;
  hex: string;
  family: string;
}

export interface ProductImage {
  url: string;
  type: 'main' | 'detail' | 'scene' | 'material' | 'dimension';
  alt: string;
}
