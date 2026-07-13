// SPDX-License-Identifier: MIT

export interface KnowledgePackage {
  id: string;
  name: string;
  type: 'brand_guide' | 'style_ref' | 'product_knowledge' | 'material_knowledge' | 'scene_ref' | 'prompt_lib';
  version: string;
  data: Record<string, unknown>;
  source: string;
  tags: string[];
  confidence: number;
  expiresAt?: string;
  createdAt: string;
}
