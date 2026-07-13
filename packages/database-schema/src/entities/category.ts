// SPDX-License-Identifier: MIT

export interface Category {
  id: string;
  name: string;
  slug: string;
  parentId: string | null;
  level: number;
  path: string;
  description: string;
  attributes: CategoryAttribute[];
}

export interface CategoryAttribute {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'enum';
  required: boolean;
  options?: string[];
}
