// SPDX-License-Identifier: MIT

import type { ExportRequest, ExportResult, ExportOptions, ExportFormat, FormatterDef } from './types';
import { getFormatter, validateOptions } from './exporters';

export class ExportEngine {
  private history: ExportResult[] = [];
  private templates: Map<string, string> = new Map();

  async export(request: ExportRequest): Promise<ExportResult> {
    const startTime = Date.now();

    const formatter = getFormatter(request.format);
    if (!formatter) {
      return this._fail(request, `Unsupported format: ${request.format}`);
    }

    const errors = validateOptions(request.format, request.options);
    if (errors.length > 0) {
      return this._fail(request, errors.join('; '));
    }

    // Simulate export process
    await new Promise(r => setTimeout(r, 100));

    const result: ExportResult = {
      id: `export-${request.projectId}-${Date.now()}`,
      format: request.format,
      url: `/exports/${request.projectId}/index.${formatter.extensions[0].replace('.', '')}`,
      size: 1024 * 1024,
      pages: 1,
      images: request.products.length * 3,
      duration: Date.now() - startTime,
      status: 'completed',
      createdAt: new Date().toISOString(),
    };

    this.history.push(result);
    return result;
  }

  registerTemplate(name: string, content: string): void {
    this.templates.set(name, content);
  }

  getTemplate(name: string): string | undefined {
    return this.templates.get(name);
  }

  getHistory(): ExportResult[] {
    return [...this.history];
  }

  getRecent(limit = 10): ExportResult[] {
    return this.history.slice(-limit).reverse();
  }

  private _fail(request: ExportRequest, error: string): ExportResult {
    return {
      id: `export-${request.projectId}-${Date.now()}`,
      format: request.format,
      url: '',
      size: 0,
      pages: 0,
      images: 0,
      duration: 0,
      status: 'failed',
      error,
      createdAt: new Date().toISOString(),
    };
  }
}
