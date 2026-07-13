// SPDX-License-Identifier: MIT

export interface SKU {
  id: string;
  productId: string;
  code: string;
  name: string;
  variants: SKUVariant[];
  price: number;
  currency: string;
  stock: number;
  images: string[];
  weight: number;
  weightUnit: 'kg' | 'g' | 'lb';
  status: 'in_stock' | 'out_of_stock' | 'discontinued';
}

export interface SKUVariant {
  name: string;
  value: string;
}
