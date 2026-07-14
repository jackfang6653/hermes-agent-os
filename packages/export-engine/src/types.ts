// SPDX-License-Identifier: MIT

export type ExportFormat = 'html' | 'pdf' | 'json' | 'zip' | 'shopify' | 'custom';

export interface ExportRequest {
  projectId: string;
  products: string[];
  format: ExportFormat;
  options: ExportOptions;
}

export interface ExportOptions {
  quality: 'draft' | 'standard' | 'high';
  includeMetadata: boolean;
  imageResolution: '720p' | '1080p' | '4k';
  watermark: boolean;
  compression: boolean;
}

export interface ExportResult {
  id: string;
  format: ExportFormat;
  url: string;
  size: number;
  pages: number;
  images: number;
  duration: number;
  status: 'completed' | 'failed' | 'processing';
  error?: string;
  createdAt: string;
}

export interface FormatterDef {
  format: ExportFormat;
  name: string;
  description: string;
  extensions: string[];
  mimeType: string;
  options: string[];
}

export interface ExportTemplate {
  id: string;
  name: string;
  format: ExportFormat;
  content: string;
  variables: string[];
  layout: string;
}
