// SPDX-License-Identifier: MIT

import type { VisionResult, MaterialAnalysis, AnalyzerConfig } from '../types.js';

export class MaterialAnalyzer {
  constructor(private config: AnalyzerConfig) {}

  async analyze(imageUrl: string): Promise<VisionResult<MaterialAnalysis>> {
    const startTime = Date.now();
    return {
      type: 'material',
      confidence: 0.7,
      data: {
        type: 'fabric',
        category: 'linen',
        texture: 'woven',
        color: 'beige',
        finish: 'matte',
        quality: 4,
        details: ['natural fiber', 'durable weave'],
      },
      raw: '',
      latency: Date.now() - startTime,
    };
  }
}
