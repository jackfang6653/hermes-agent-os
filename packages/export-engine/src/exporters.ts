// SPDX-License-Identifier: MIT

import type { FormatterDef, ExportOptions } from './types.js';

export const FORMATTERS: FormatterDef[] = [
  {
    format: 'html',
    name: 'Responsive HTML',
    description: 'Self-contained HTML page with embedded styles',
    extensions: ['.html', '.htm'],
    mimeType: 'text/html',
    options: ['includeMetadata', 'watermark'],
  },
  {
    format: 'pdf',
    name: 'PDF Document',
    description: 'Print-ready PDF with vector graphics',
    extensions: ['.pdf'],
    mimeType: 'application/pdf',
    options: ['quality', 'watermark'],
  },
  {
    format: 'json',
    name: 'JSON Data',
    description: 'Structured product data in JSON format',
    extensions: ['.json'],
    mimeType: 'application/json',
    options: ['includeMetadata'],
  },
  {
    format: 'zip',
    name: 'ZIP Archive',
    description: 'Compressed archive with all assets',
    extensions: ['.zip'],
    mimeType: 'application/zip',
    options: ['imageResolution', 'compression'],
  },
  {
    format: 'shopify',
    name: 'Shopify Upload',
    description: 'Shopify-compatible product data and images',
    extensions: ['.csv', '.zip'],
    mimeType: 'application/zip',
    options: ['includeMetadata', 'imageResolution'],
  },
];

export function getFormatter(format: string): FormatterDef | undefined {
  return FORMATTERS.find(f => f.format === format);
}

export function validateOptions(format: string, options: ExportOptions): string[] {
  const formatter = getFormatter(format);
  if (!formatter) return ['Unknown format'];

  const errors: string[] = [];
  for (const opt of Object.keys(options)) {
    if (!formatter.options.includes(opt)) {
      // Option not in formatter list — still acceptable, just ignored
    }
  }
  return errors;
}
