// SPDX-License-Identifier: MIT

import type { DNASchema, BrandProfile } from './types.js';

/**
 * 从产品视觉分析结果自动蒸馏品牌DNA
 * 输入: GPT-4o Vision 的结构化产品特征
 * 输出: 匹配的品牌 DNA Schema
 */
export function distillDNA(
  productFeatures: {
    style_keywords?: string[];
    materials?: string[];
    colors?: string[];
    atmosphere?: string[];
    craftsmanship?: string;
    category?: string;
  },
  knownProfile?: Partial<BrandProfile>,
): DNASchema {
  const styles = productFeatures.style_keywords ?? knownProfile?.style ?? ['nordic'];
  const atmosphere = productFeatures.atmosphere ?? knownProfile?.positioning ?? ['calm', 'warm', 'refined'];

  // Auto-map color palette from detected colors
  const colorPalette = mapColorsToPalette(productFeatures.colors);

  return {
    visual: {
      style: styles[0] ?? 'nordic',
      atmosphere,
      colorPalette,
    },
    preserve: {
      productGeometry: true,
      materialTexture: true,
      colorAccuracy: true,
    },
    variable: {
      camera: true,
      scene: true,
      composition: true,
    },
  };
}

/**
 * 验证产品特征是否符合品牌DNA
 * 返回 结构化评估 + 改进建议
 */
export function evaluateBrandFit(
  dna: DNASchema,
  features: {
    style_keywords?: string[];
    colors?: string[];
    atmosphere?: string[];
    materials?: string[];
  },
): { score: number; matched: string[]; gaps: string[]; suggestions: string[] } {
  const matched: string[] = [];
  const gaps: string[] = [];
  const suggestions: string[] = [];

  // Style match
  const primaryStyle = dna.visual.style.toLowerCase();
  if (features.style_keywords?.some(s => s.toLowerCase().includes(primaryStyle))) {
    matched.push(`Style matches brand (${primaryStyle})`);
  } else {
    gaps.push(`Style doesn't match brand direction (${primaryStyle})`);
    suggestions.push(`Adjust styling toward ${primaryStyle}: clean lines, natural materials, minimal ornamentation`);
  }

  // Atmosphere match
  for (const mood of dna.visual.atmosphere) {
    if (features.atmosphere?.some(a => a.toLowerCase().includes(mood))) {
      matched.push(`Atmosphere aligns with brand: ${mood}`);
      break;
    }
  }

  // Color check
  const brandColors = dna.visual.colorPalette.map(c => c.toLowerCase());
  const featureColors = features.colors?.map(c => c.toLowerCase()) ?? [];
  const colorMatch = featureColors.some(fc => brandColors.some(bc => colorDistance(fc, bc) < 0.2));
  if (colorMatch) {
    matched.push('Colors are within brand palette');
  } else if (features.colors?.length) {
    gaps.push('Detected colors fall outside brand palette');
    suggestions.push(`Use brand palette: ${dna.visual.colorPalette.join(', ')}`);
  }

  const score = matched.length / Math.max(matched.length + gaps.length, 1);
  return { score, matched, gaps, suggestions };
}

function mapColorsToPalette(colors?: string[]): string[] {
  if (!colors?.length) return ['#f5f0e8', '#d4c5b0', '#8b7355'];
  const colorMap: Record<string, string> = {
    beige: '#f5f0e8', cream: '#fdf6e3', tan: '#d4c5b0',
    brown: '#8b7355', dark: '#2c2c2c', black: '#2c2c2c',
    white: '#f5f0e8', grey: '#a0a0a0', gray: '#a0a0a0',
    wood: '#c4a882', oak: '#c4a882', walnut: '#8b7355',
    green: '#8a9a7a', blue: '#7a8a9a', rust: '#c4a882',
  };
  const palette = colors.map(c => colorMap[c.toLowerCase().split(' ')[0]]).filter(Boolean);
  return palette.length >= 2 ? Array.from(new Set(palette)).slice(0, 4) : ['#f5f0e8', '#d4c5b0', '#8b7355'];
}

function colorDistance(c1: string, c2: string): number {
  const h1 = c1.replace('#', '');
  const h2 = c2.replace('#', '');
  if (h1.length < 6 || h2.length < 6) return 1;
  const r1 = parseInt(h1.slice(0, 2), 16), g1 = parseInt(h1.slice(2, 4), 16), b1 = parseInt(h1.slice(4, 6), 16);
  const r2 = parseInt(h2.slice(0, 2), 16), g2 = parseInt(h2.slice(2, 4), 16), b2 = parseInt(h2.slice(4, 6), 16);
  const dist = Math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2);
  return dist / Math.sqrt(3 * 255 ** 2);
}
