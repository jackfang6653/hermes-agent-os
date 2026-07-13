// SPDX-License-Identifier: MIT

import type { StepDef, WorkflowDef } from './types.js';

export function createNorhorPipeline(): WorkflowDef {
  return {
    id: 'norhor-detail-gen',
    name: 'NORHOR Detail Page Generation',
    description: 'End-to-end pipeline for NORHOR product detail pages',
    version: '1.0.0',
    steps: [
      {
        id: 'analyze_product',
        name: 'Product Analysis',
        type: 'analyze',
        config: { model: 'gpt-4o', fields: ['category', 'materials', 'colors', 'dimensions'] },
        dependsOn: [],
        timeout: 30000,
        retry: { maxAttempts: 2, delay: 1000 },
      },
      {
        id: 'extract_dna',
        name: 'Brand DNA Extraction',
        type: 'extract_dna',
        config: { brand: 'NORHOR', preserveRules: true },
        dependsOn: ['analyze_product'],
        timeout: 10000,
        retry: { maxAttempts: 1, delay: 500 },
      },
      {
        id: 'create_scene',
        name: 'Scene Selection',
        type: 'create_scene',
        config: { style: 'nordic', maxScenes: 3 },
        dependsOn: ['analyze_product', 'extract_dna'],
        timeout: 15000,
        retry: { maxAttempts: 1, delay: 500 },
      },
      {
        id: 'compile_prompt',
        name: 'Prompt Compilation',
        type: 'compile_prompt',
        config: { templates: ['product-main', 'scene-lifestyle'] },
        dependsOn: ['analyze_product', 'create_scene'],
        timeout: 10000,
        retry: { maxAttempts: 1, delay: 500 },
      },
      {
        id: 'generate_image',
        name: 'Image Generation',
        type: 'generate_image',
        config: { model: 'flux', batchSize: 3 },
        dependsOn: ['compile_prompt'],
        timeout: 120000,
        retry: { maxAttempts: 3, delay: 2000 },
      },
      {
        id: 'qa_check',
        name: 'Quality Check',
        type: 'qa_check',
        config: { checks: ['brand_compliance', 'image_quality', 'resolution'] },
        dependsOn: ['generate_image'],
        timeout: 20000,
        retry: { maxAttempts: 1, delay: 500 },
      },
      {
        id: 'export',
        name: 'Export Package',
        type: 'export',
        config: { format: ['html', 'zip'], includeMetadata: true },
        dependsOn: ['qa_check'],
        timeout: 30000,
        retry: { maxAttempts: 2, delay: 1000 },
      },
    ],
    onError: 'abort',
  };
}
