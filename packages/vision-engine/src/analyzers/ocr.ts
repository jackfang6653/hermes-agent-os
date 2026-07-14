// SPDX-License-Identifier: MIT

import type { VisionResult, OCRResult, AnalyzerConfig } from '../types.js';

export class OCRAnalyzer {
  constructor(private config: AnalyzerConfig) {}

  async analyze(imageUrl: string): Promise<VisionResult<OCRResult>> {
    const startTime = Date.now();
    return {
      type: 'ocr',
      confidence: 0.8,
      data: {
        text: '',
        blocks: [],
        language: 'zh',
      },
      raw: '',
      latency: Date.now() - startTime,
    };
  }
}
