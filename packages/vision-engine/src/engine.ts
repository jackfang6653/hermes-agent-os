// SPDX-License-Identifier: MIT

import type { AnalysisType, VisionResult, AnalyzerConfig } from './types.js';
import { ProductAnalyzer } from './analyzers/product-analyzer.js';
import { MaterialAnalyzer } from './analyzers/material-analyzer.js';
import { ColorAnalyzer } from './analyzers/color-analyzer.js';
import { OCRAnalyzer } from './analyzers/ocr.js';

export class VisionEngine {
  private analyzers: Map<AnalysisType, any>;
  private config: AnalyzerConfig;

  constructor(config: AnalyzerConfig = {}) {
    this.config = config;
    this.analyzers = new Map();
    this.analyzers.set('product', new ProductAnalyzer(config));
    this.analyzers.set('material', new MaterialAnalyzer(config));
    this.analyzers.set('color', new ColorAnalyzer(config));
    this.analyzers.set('ocr', new OCRAnalyzer(config));
  }

  async analyze<T = any>(imageUrl: string, type: AnalysisType): Promise<VisionResult<T>> {
    const analyzer = this.analyzers.get(type);
    if (!analyzer) throw new Error(`No analyzer for type: ${type}`);
    return analyzer.analyze(imageUrl) as Promise<VisionResult<T>>;
  }

  async analyzeAll(imageUrl: string): Promise<Map<AnalysisType, VisionResult>> {
    const results = new Map<AnalysisType, VisionResult>();
    const types = Array.from(this.analyzers.keys());
    const promises = types.map(async (type) => {
      try {
        const result = await this.analyze(imageUrl, type);
        results.set(type, result);
      } catch {
        // skip failed analyzer
      }
    });
    await Promise.all(promises);
    return results;
  }
}
