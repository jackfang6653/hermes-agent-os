// SPDX-License-Identifier: MIT

import type { QAReport, QACheck, QAConfig, QARule, QAReportType, BrandComplianceCheck, ImageQualityCheck } from './types.js';
import { DEFAULT_CONFIG } from './rules.js';

export class QAEngine {
  private config: QAConfig;

  constructor(config?: Partial<QAConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  async runCheck(
    type: QAReportType,
    targetId: string,
    targetType: QAReport['targetType'],
    data: Record<string, unknown>,
  ): Promise<QAReport> {
    const startTime = Date.now();
    const checks: QACheck[] = [];

    const applicableRules = this.config.rules.filter(
      r => r.category === type && r.enabled,
    );

    for (const rule of applicableRules) {
      const check = this._evaluateRule(rule, data);
      checks.push(check);
    }

    const weights = checks.reduce((sum, c) => sum + c.weight, 0);
    const score = weights > 0
      ? checks.reduce((sum, c) => sum + (c.status === 'pass' ? c.weight : 0), 0) / weights
      : 1;

    const failed = checks.filter(c => c.status === 'fail');
    const passed = checks.every(c => c.status !== 'fail') && score >= this.config.minScore;

    return {
      id: `qa-${targetId}-${Date.now()}`,
      type,
      targetId,
      targetType,
      score,
      checks,
      summary: failed.length > 0
        ? `Failed ${failed.length} of ${checks.length} checks (score: ${(score * 100).toFixed(0)}%)`
        : `All ${checks.length} checks passed (score: ${(score * 100).toFixed(0)}%)`,
      passed,
      createdAt: new Date().toISOString(),
      duration: Date.now() - startTime,
    };
  }

  async checkBrandCompliance(data: Record<string, unknown>): Promise<BrandComplianceCheck> {
    return {
      brandId: String(data.brandId ?? ''),
      styleMatch: String(data.style ?? '').toLowerCase() !== 'industrial',
      colorPaletteValid: !data.prohibitedColor,
      lightingValid: String(data.lighting ?? '').includes('natural') || String(data.lighting ?? '').includes('warm'),
      prohibitedContent: data.prohibitedContent ? [String(data.prohibitedContent)] : [],
    };
  }

  async checkImageQuality(data: Record<string, unknown>): Promise<ImageQualityCheck> {
    return {
      resolution: {
        width: Number(data.width ?? 1024),
        height: Number(data.height ?? 1024),
      },
      format: String(data.format ?? 'png'),
      fileSize: Number(data.fileSize ?? 0),
      dpi: Number(data.dpi ?? 72),
      blurDetected: data.blurred === true,
      noiseLevel: Number(data.noise ?? 0),
      artifacts: data.artifacts ? [String(data.artifacts)] : [],
    };
  }

  updateConfig(partial: Partial<QAConfig>): void {
    this.config = { ...this.config, ...partial };
  }

  getConfig(): QAConfig {
    return { ...this.config };
  }

  private _evaluateRule(
    rule: QARule,
    data: Record<string, unknown>,
  ): QACheck {
    // Simplified rule evaluation
    const value = data[rule.id.replace(/-/g, '_')];
    const status = value === undefined || value === true || value === null
      ? 'pass'
      : rule.severity === 'error' ? 'fail' : 'warn';

    return {
      name: rule.name,
      status,
      message: status === 'pass' ? `${rule.name}: OK` : `${rule.name}: ${rule.severity}`,
      weight: rule.severity === 'error' ? 2 : 1,
    };
  }
}
