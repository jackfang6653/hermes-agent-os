// SPDX-License-Identifier: MIT

import { BrandEngine } from '@hermes-os/brand-engine';
import { WorkflowEngine } from '@hermes-os/workflow-engine';
import { PromptCompiler, PRODUCT_PROMPT, SCENE_PROMPT, DETAIL_PROMPT } from '@hermes-os/prompt-compiler';
import { NORHOR_PROFILE, SCENE_PRESETS } from './presets.js';
import type { SceneId, CategoryId } from './presets.js';

export interface GenerateOptions {
  sku: string;
  productName: string;
  category: CategoryId;
  material: string;
  color: string;
  scene?: SceneId;
  style?: string;
}

export interface ProductResult {
  sku: string;
  imagePrompts: { type: string; prompt: string; negativePrompt: string }[];
  brandScore: number;
  scene: string;
}

export class NorhorPipeline {
  private brandEngine: BrandEngine;
  private compiler: PromptCompiler;
  private engine: WorkflowEngine;

  constructor() {
    this.brandEngine = BrandEngine.createNORHOREngine();
    this.engine = new WorkflowEngine();
    this.compiler = new PromptCompiler();

    // Register NORHOR prompt templates
    this.compiler.register(PRODUCT_PROMPT);
    this.compiler.register(SCENE_PROMPT);
    this.compiler.register(DETAIL_PROMPT);
  }

  async generateProduct(options: GenerateOptions): Promise<ProductResult> {
    const sceneId = options.scene ?? 'nordic_living';
    const scene = SCENE_PRESETS[sceneId];
    const style = options.style ?? 'nordic';

    // 1. Validate against brand
    const validation = this.brandEngine.validate('norhor', {
      style,
      color: options.color,
      lighting: scene.lighting.type,
      geometryChanged: false,
    });

    // 2. Compile prompts
    const productPrompt = this.compiler.compile('product-main', {
      style,
      product_type: options.category,
      material: options.material,
      color: options.color,
      lighting: scene.lighting.type,
      background: 'neutral',
      atmosphere: scene.moodKeywords[0],
    });

    const scenePrompt = this.compiler.compile('scene-lifestyle', {
      scene_style: style,
      room_type: scene.name,
      product_type: options.productName,
      product_color: options.color,
      lighting: scene.lighting.type,
      color_palette: scene.colorPalette.join(', '),
      decoration_style: 'minimal',
      atmosphere: scene.moodKeywords[0],
    });

    const detailPrompt = this.compiler.compile('detail-story', {
      product_type: options.productName,
      style,
      feature_focus: 'material texture and craftsmanship',
      material: options.material,
      texture: 'woven',
      color: options.color,
      atmosphere: scene.moodKeywords[0],
    });

    return {
      sku: options.sku,
      imagePrompts: [
        { type: 'product_main', prompt: productPrompt.prompt, negativePrompt: productPrompt.negativePrompt },
        { type: 'scene_lifestyle', prompt: scenePrompt.prompt, negativePrompt: scenePrompt.negativePrompt },
        { type: 'detail_story', prompt: detailPrompt.prompt, negativePrompt: detailPrompt.negativePrompt },
      ],
      brandScore: validation.score,
      scene: sceneId,
    };
  }

  getBrandEngine(): BrandEngine {
    return this.brandEngine;
  }

  getWorkflowEngine(): WorkflowEngine {
    return this.engine;
  }

  getPromptCompiler(): PromptCompiler {
    return this.compiler;
  }

  validateBrand(style: string, color: string, lighting: string) {
    return this.brandEngine.validate('norhor', { style, color, lighting, geometryChanged: false });
  }
}
