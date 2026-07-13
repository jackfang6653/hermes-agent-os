// SPDX-License-Identifier: MIT

export interface ExportConfig {
  id: string;
  name: string;
  format: ExportFormat;
  options: ExportOptions;
  destinations: ExportDestination[];
}

export type ExportFormat = 'html' | 'pdf' | 'json' | 'zip' | 'shopify' | 'custom';

export interface ExportOptions {
  quality: 'draft' | 'standard' | 'high';
  includeMetadata: boolean;
  imageResolution: '720p' | '1080p' | '4k';
  watermark: boolean;
  compression: boolean;
}

export interface ExportDestination {
  type: 'local' | 's3' | 'ftp' | 'api' | 'webhook';
  config: Record<string, unknown>;
}
