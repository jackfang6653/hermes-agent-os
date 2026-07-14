// SPDX-License-Identifier: MIT

export type QAReportType = 'brand_compliance' | 'image_quality' | 'layout' | 'content_review' | 'performance';

export interface QAReport {
  id: string;
  type: QAReportType;
  targetId: string;
  targetType: 'product' | 'image' | 'scene' | 'page';
  score: number;
  checks: QACheck[];
  summary: string;
  passed: boolean;
  createdAt: string;
  duration: number;
}

export interface QACheck {
  name: string;
  status: 'pass' | 'fail' | 'warn' | 'skip';
  message: string;
  details?: Record<string, unknown>;
  weight: number;
}

export interface QARule {
  id: string;
  name: string;
  category: QAReportType;
  condition: string;
  severity: 'error' | 'warn';
  enabled: boolean;
}

export interface QAConfig {
  autoRun: boolean;
  strictMode: boolean;
  minScore: number;
  rules: QARule[];
  reportPath: string;
}

export interface BrandComplianceCheck {
  brandId: string;
  styleMatch: boolean;
  colorPaletteValid: boolean;
  lightingValid: boolean;
  prohibitedContent: string[];
}

export interface ImageQualityCheck {
  resolution: { width: number; height: number };
  format: string;
  fileSize: number;
  dpi: number;
  blurDetected: boolean;
  noiseLevel: number;
  artifacts: string[];
}

export interface LayoutCheck {
  elementCount: number;
  alignment: number;
  whitespace: number;
  readability: number;
  consistency: number;
}
