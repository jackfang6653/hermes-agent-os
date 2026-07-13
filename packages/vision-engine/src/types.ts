// SPDX-License-Identifier: MIT

export type AnalysisType = 'product' | 'scene' | 'material' | 'color' | 'layout' | 'ocr';

export interface VisionResult<T = Record<string, unknown>> {
  type: AnalysisType;
  confidence: number;
  data: T;
  raw: string;
  latency: number;
}

export interface ProductRecognition {
  category: string;
  subcategory?: string;
  name: string;
  structure: string[];
  materials: string[];
  colors: string[];
  dimensions?: { width: number; height: number; depth: number };
}

export interface MaterialAnalysis {
  type: string;
  category: string;
  texture: string;
  color: string;
  finish: string;
  quality: number;
  details: string[];
}

export interface ColorAnalysis {
  dominantColor: string;
  palette: string[];
  hexValues: string[];
  contrast: number;
  warmth: 'warm' | 'cool' | 'neutral';
}

export interface SceneAnalysis {
  style: string;
  atmosphere: string[];
  lighting: string;
  composition: string;
  objects: string[];
  colorPalette: string[];
}

export interface LayoutAnalysis {
  elements: LayoutElement[];
  composition: string;
  focalPoint: { x: number; y: number };
  balance: 'symmetric' | 'asymmetric' | 'radial';
}

export interface LayoutElement {
  type: string;
  bounds: { x: number; y: number; width: number; height: number };
  label: string;
}

export interface OCRResult {
  text: string;
  blocks: OCRBlock[];
  language: string;
}

export interface OCRBlock {
  text: string;
  confidence: number;
  bounds: { x: number; y: number; width: number; height: number };
}

export interface AnalyzerConfig {
  modelProvider?: string;
  modelName?: string;
  apiKey?: string;
  baseUrl?: string;
}
