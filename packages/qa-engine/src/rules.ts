// SPDX-License-Identifier: MIT

import type { QARule, QAReportType } from './types.js';

export const DEFAULT_RULES: QARule[] = [
  // Brand compliance
  { id: 'brand-style', name: 'Brand style match', category: 'brand_compliance', condition: 'style must match brand DNA', severity: 'error', enabled: true },
  { id: 'brand-colors', name: 'Brand color palette', category: 'brand_compliance', condition: 'colors must be in brand palette or accent colors', severity: 'error', enabled: true },
  { id: 'brand-lighting', name: 'Lighting compliance', category: 'brand_compliance', condition: 'lighting must be natural or warm ambient', severity: 'warn', enabled: true },

  // Image quality
  { id: 'img-resolution', name: 'Minimum resolution', category: 'image_quality', condition: 'resolution >= 1024x1024', severity: 'error', enabled: true },
  { id: 'img-format', name: 'Valid format', category: 'image_quality', condition: 'format must be PNG or JPEG', severity: 'warn', enabled: true },
  { id: 'img-blur', name: 'Blur detection', category: 'image_quality', condition: 'no significant blur', severity: 'error', enabled: true },

  // Layout
  { id: 'layout-readability', name: 'Readability score', category: 'layout', condition: 'readability >= 0.7', severity: 'warn', enabled: true },
  { id: 'layout-consistency', name: 'Design consistency', category: 'layout', condition: 'consistency >= 0.6', severity: 'warn', enabled: true },

  // Content
  { id: 'content-grammar', name: 'Grammar check', category: 'content_review', condition: 'no grammar errors', severity: 'warn', enabled: true },
  { id: 'content-brand-voice', name: 'Brand voice', category: 'content_review', condition: 'tone matches brand guidelines', severity: 'error', enabled: true },
];

export const DEFAULT_CONFIG = {
  autoRun: true,
  strictMode: false,
  minScore: 0.7,
  rules: DEFAULT_RULES,
  reportPath: './reports',
};
