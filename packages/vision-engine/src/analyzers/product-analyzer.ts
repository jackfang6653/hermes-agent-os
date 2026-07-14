// SPDX-License-Identifier: MIT

import type { VisionResult, ProductRecognition, MaterialAnalysis, ColorAnalysis, AnalyzerConfig } from '../types.js';

interface VisionCallResult {
  content: string;
  usage?: { promptTokens: number; completionTokens: number };
}

function parseJSON<T>(content: string, fallback: T): T {
  try {
    const start = content.indexOf('{');
    const end = content.lastIndexOf('}');
    if (start >= 0 && end > start) return JSON.parse(content.slice(start, end + 1));
  } catch { /* ignore */ }
  return fallback;
}

async function callVision(
  imageUrl: string,
  instruction: string,
  config: AnalyzerConfig,
): Promise<VisionCallResult> {
  const apiKey = config.apiKey ?? process.env['OPENAI_API_KEY'];
  const model = config.modelName ?? 'gpt-4o';
  const baseUrl = config.baseUrl ?? 'https://api.openai.com/v1';

  if (!apiKey) {
    console.warn('OPENAI_API_KEY not configured — returning mock data');
    return { content: '' };
  }

  const body = {
    model,
    messages: [{
      role: 'user',
      content: [
        { type: 'text', text: instruction },
        { type: 'image_url', image_url: { url: imageUrl, detail: 'high' } },
      ],
    }],
    max_tokens: 2048,
    temperature: 0.1,
    response_format: { type: 'json_object' },
  };

  try {
    const res = await fetch(`${baseUrl}/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${apiKey}` },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`GPT-4o Vision error ${res.status}`);
    const data = await res.json() as any;
    return {
      content: data.choices?.[0]?.message?.content ?? '',
      usage: data.usage ? { promptTokens: data.usage.prompt_tokens, completionTokens: data.usage.completion_tokens } : undefined,
    };
  } catch (e: any) {
    console.warn(`Vision API call failed (${e.message}), using fallback`);
    return { content: '' };
  }
}

export class ProductAnalyzer {
  constructor(private config: AnalyzerConfig) {}

  async analyze(imageUrl: string): Promise<VisionResult<ProductRecognition>> {
    const startTime = Date.now();
    const result = await callVision(imageUrl, `Analyze this product image for e-commerce detail page generation.
Return JSON with:
- category: product category (sofa/chair/table/cabinet/bed/lighting/other)
- subcategory: more specific type
- name: product name suggestion
- structure: array of visible structural elements
- materials: array of visible material names
- colors: array of dominant color names
- dimensions_guess: estimated proportions {width,height,depth} in cm (null if unknown)
- style_keywords: array of style descriptors (nordic/minimal/modern/scandinavian/industrial/other)
- craftsmanship: visible craftsmanship details
- atmosphere: mood/atmosphere keywords`, this.config);

    const data = parseJSON(result.content, {} as any);
    return {
      type: 'product',
      confidence: result.content ? 0.85 : 0,
      data: {
        category: data.category ?? 'unknown',
        subcategory: data.subcategory,
        name: data.name ?? 'Product',
        structure: data.structure ?? [],
        materials: data.materials ?? [],
        colors: data.colors ?? [],
        dimensions: data.dimensions_guess,
      },
      raw: result.content,
      latency: Date.now() - startTime,
    };
  }
}

export class MaterialAnalyzer {
  constructor(private config: AnalyzerConfig) {}

  async analyze(imageUrl: string): Promise<VisionResult<MaterialAnalysis>> {
    const startTime = Date.now();
    const result = await callVision(imageUrl, `Analyze the materials in this product image.
Return JSON with:
- type: material type name
- category: wood/fabric/metal/stone/leather/glass/ceramic/composite
- texture: surface texture descriptor
- color: primary color name
- finish: matte/glossy/polished/brushed/raw
- quality: 1-5 rating
- details: array of material detail descriptors`, this.config);

    const data = parseJSON(result.content, {} as any);
    return {
      type: 'material',
      confidence: result.content ? 0.8 : 0,
      data: {
        type: data.type ?? 'unknown',
        category: data.category ?? 'fabric',
        texture: data.texture ?? 'smooth',
        color: data.color ?? 'neutral',
        finish: data.finish ?? 'matte',
        quality: data.quality ?? 3,
        details: data.details ?? [],
      },
      raw: result.content,
      latency: Date.now() - startTime,
    };
  }
}

export class ColorAnalyzer {
  constructor(private config: AnalyzerConfig) {}

  async analyze(imageUrl: string): Promise<VisionResult<ColorAnalysis>> {
    const startTime = Date.now();
    const result = await callVision(imageUrl, `Analyze the color composition of this product image.
Return JSON with:
- dominantColor: hex code of the most prominent color
- palette: array of 4-6 hex color codes forming the product's color palette
- contrast: contrast level 0-1
- warmth: warm/cool/neutral`, this.config);

    const data = parseJSON(result.content, {
      dominantColor: '#808080',
      palette: ['#808080'],
      hexValues: ['#808080'],
      contrast: 0.5,
      warmth: 'neutral' as const,
    });
    return {
      type: 'color',
      confidence: result.content ? 0.9 : 0,
      data: {
        dominantColor: data.dominantColor ?? '#808080',
        palette: data.palette ?? [],
        hexValues: data.palette ?? [],
        contrast: data.contrast ?? 0.5,
        warmth: data.warmth ?? 'neutral',
      },
      raw: result.content,
      latency: Date.now() - startTime,
    };
  }
}
