// SPDX-License-Identifier: MIT

import { BrandEngine, distillDNA, evaluateBrandFit } from '@hermes-os/brand-engine';
import { WorkflowEngine, createNorhorPipeline as __createNorhorPipeline } from '@hermes-os/workflow-engine';
import { PromptCompiler, PRODUCT_PROMPT, SCENE_PROMPT, DETAIL_PROMPT } from '@hermes-os/prompt-compiler';
import { VisionEngine } from '@hermes-os/vision-engine';
import { NORHOR_PROFILE, SCENE_PRESETS, PRODUCT_CATEGORIES } from './presets.js';
import { generateImage } from './image-gen.js';
import type { SceneId, CategoryId } from './presets.js';

export interface GenerateOptions {
  sku: string;
  productName: string;
  category: CategoryId;
  material: string;
  color: string;
  scene?: SceneId;
  style?: string;
  imageUrl?: string;
  openAiKey?: string;
}

export interface ProductResult {
  sku: string;
  imagePrompts: { type: string; prompt: string; negativePrompt: string }[];
  brandScore: number;
  brandFit: { matched: string[]; gaps: string[]; suggestions: string[] };
  scene: string;
  analysis?: any;
  detailPage?: string;
}

export class NorhorPipeline {
  private brandEngine: BrandEngine;
  private compiler: PromptCompiler;
  private engine: WorkflowEngine;
  private vision: VisionEngine;

  constructor(openAiKey?: string) {
    this.brandEngine = BrandEngine.createNORHOREngine();
    this.engine = new WorkflowEngine();
    this.compiler = new PromptCompiler();
    this.vision = new VisionEngine({ apiKey: openAiKey, modelName: 'gpt-4o' });

    this.compiler.register(PRODUCT_PROMPT);
    this.compiler.register(SCENE_PROMPT);
    this.compiler.register(DETAIL_PROMPT);
  }

  async generateProduct(options: GenerateOptions): Promise<ProductResult> {
    const sceneId = options.scene ?? 'nordic_living';
    const scene = SCENE_PRESETS[sceneId];
    const style = options.style ?? 'nordic';

    // ── Step 1: Vision Analysis (real GPT-4o) ──────────────
    let analysis: any = {};
    let detectedFeatures: Record<string, any> = {};

    if (options.imageUrl) {
      try {
        const productResult = await this.vision.analyze(options.imageUrl, 'product');
        analysis.product = productResult.data;

        const colorResult = await this.vision.analyze(options.imageUrl, 'color');
        analysis.color = colorResult.data;

        detectedFeatures = {
          style_keywords: [style, ...(productResult.data.structure ?? [])],
          materials: productResult.data.materials ?? [options.material],
          colors: productResult.data.colors ?? [options.color],
          atmosphere: scene.moodKeywords,
          category: productResult.data.category ?? options.category,
        };
      } catch (e: any) {
        console.warn(`Vision analysis failed (${e.message}), using provided params`);
        detectedFeatures = {
          style_keywords: [style],
          materials: [options.material],
          colors: [options.color],
          atmosphere: scene.moodKeywords,
          category: options.category,
        };
      }
    }

    // ── Step 2: Auto DNA Distillation ─────────────────────
    const distilledDNA = distillDNA(detectedFeatures, NORHOR_PROFILE);

    // ── Step 3: Brand Fit Evaluation ──────────────────────
    const brandFit = evaluateBrandFit(distilledDNA, detectedFeatures);

    // ── Step 4: Compile Prompts with DNAd values ──────────
    const actualStyle = distilledDNA.visual.style;
    const actualColors = distilledDNA.visual.colorPalette;
    const actualAtmosphere = distilledDNA.visual.atmosphere[0];

    const productPrompt = this.compiler.compile('product-main', {
      style: actualStyle,
      product_type: options.category,
      material: options.material,
      color: analysis.product?.colors?.[0] ?? options.color,
      lighting: scene.lighting.type,
      background: 'neutral',
      atmosphere: actualAtmosphere,
    });

    const scenePrompt = this.compiler.compile('scene-lifestyle', {
      scene_style: actualStyle,
      room_type: scene.name,
      product_type: options.productName,
      product_color: analysis.product?.colors?.[0] ?? options.color,
      lighting: scene.lighting.type,
      color_palette: actualColors.join(', '),
      decoration_style: 'minimal',
      atmosphere: actualAtmosphere,
    });

    const detailPrompt = this.compiler.compile('detail-story', {
      product_type: options.productName,
      style: actualStyle,
      feature_focus: 'material texture and craftsmanship',
      material: options.material,
      texture: analysis.product?.structure?.[0] ?? 'woven',
      color: analysis.product?.colors?.[0] ?? options.color,
      atmosphere: actualAtmosphere,
    });

    // ── Step 5: Generate Detail Page HTML ─────────────────
    const detailPage = buildDetailPageHTML({
      sku: options.sku,
      productName: options.productName,
      category: options.category,
      material: options.material,
      colors: analysis.product?.colors ?? [options.color],
      palette: actualColors,
      scene: scene.name,
      style: actualStyle,
      brandScore: brandFit.score,
      prompts: productPrompt.prompt,
    });

    return {
      sku: options.sku,
      imagePrompts: [
        { type: 'product_main', prompt: productPrompt.prompt, negativePrompt: productPrompt.negativePrompt },
        { type: 'scene_lifestyle', prompt: scenePrompt.prompt, negativePrompt: scenePrompt.negativePrompt },
        { type: 'detail_story', prompt: detailPrompt.prompt, negativePrompt: detailPrompt.negativePrompt },
      ],
      brandScore: brandFit.score,
      brandFit: { matched: brandFit.matched, gaps: brandFit.gaps, suggestions: brandFit.suggestions },
      scene: sceneId,
      analysis,
      detailPage,
    };
  }

  getBrandEngine() { return this.brandEngine; }
  getWorkflowEngine() { return this.engine; }
  getPromptCompiler() { return this.compiler; }
  getVisionEngine() { return this.vision; }

  /**
   * 注册完整的 7 步 NORHOR 流水线并返回 engine
   * 步骤: analyze → extract_dna → create_scene → compile_prompt → generate_image → qa_check → export
   */
  createE2EWorkflow() {
    const wf = __createNorhorPipeline();
    this.engine.register(wf);

    this.engine.registerHandler('analyze', async (step, ctx) => {
      const result = await this.generateProduct(ctx as any);
      return { ...result, status: 'analyzed' };
    });

    this.engine.registerHandler('extract_dna', async (_step, ctx: any) => {
      const features = ctx['analyze_product']?.analysis?.product ?? {};
      const dna = distillDNA(features, NORHOR_PROFILE);
      return { dna, score: evaluateBrandFit(dna, features) };
    });

    this.engine.registerHandler('create_scene', async (_step, ctx: any) => {
      const analysis = ctx['analyze_product']?.analysis?.product ?? {};
      const category = analysis.category ?? 'living';
      const sceneId = (Object.keys(SCENE_PRESETS).find((id): id is SceneId => {
        const cat = PRODUCT_CATEGORIES.find(c => c.id === category);
        return cat ? (cat.scenes as readonly string[]).includes(id) : false;
      }) ?? 'nordic_living') as SceneId;
      return { sceneId, scene: SCENE_PRESETS[sceneId] };
    });

    this.engine.registerHandler('compile_prompt', async (_step, ctx: any) => {
      return { prompts: ctx['analyze_product']?.imagePrompts ?? [] };
    });

    this.engine.registerHandler('generate_image', async (_step, ctx: any) => {
      const prompts = ctx['compile_prompt']?.prompts ?? [];
      const results = [];
      for (const p of prompts.slice(0, 1)) {
        const img = await generateImage(p.prompt, { provider: 'openai' }, p.negativePrompt);
        results.push(img);
      }
      return { images: results };
    });

    this.engine.registerHandler('qa_check', async (_step, ctx) => {
      const result = ctx['analyze_product'] as any;
      return { passed: result?.brandScore >= 0.5, score: result?.brandScore ?? 0 };
    });

    this.engine.registerHandler('export', async (_step, ctx) => {
      const result = ctx['analyze_product'] as any;
      return { html: result?.detailPage ?? '', format: 'html', status: 'exported' };
    });

    return wf;
  }
}

function buildDetailPageHTML(data: {
  sku: string; productName: string; category: string;
  material: string; colors: string[]; palette: string[];
  scene: string; style: string; brandScore: number; prompts: string;
}): string {
  const paletteCss = data.palette.map((c, i) => `.swatch-${i} { background: ${c}; }`).join('\n  ');
  return `<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>${data.productName} — NORHOR 北欧表情</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: 'Inter','Segoe UI',sans-serif; color:#2c2c2c; background:#faf9f7; }
.hero { width:100%; height:80vh; background:linear-gradient(135deg,${data.palette[0]},${data.palette[1]??data.palette[0]}); display:flex; align-items:center; justify-content:center; }
.hero h1 { font-size:3rem; font-weight:300; color:#2c2c2c; letter-spacing:-0.02em; }
.content { max-width:1200px; margin:0 auto; padding:4rem 2rem; }
.grid { display:grid; grid-template-columns:1fr 1fr; gap:2rem; }
.detail-card { background:#fff; padding:2rem; border-radius:8px; }
.detail-card h3 { font-size:1.2rem; font-weight:500; margin-bottom:1rem; color:#8b7355; }
.palette { display:flex; gap:0.5rem; margin:1rem 0; }
.swatch { width:2rem; height:2rem; border-radius:50%; border:1px solid #e0ddd8; }
.score { display:inline-block; padding:0.25rem 0.75rem; border-radius:999px; font-size:0.85rem; }
.score-high { background:#e8f5e9; color:#2e7d32; }
.score-mid { background:#fff3e0; color:#e65100; }
.score-low { background:#ffebee; color:#c62828; }
.tag { display:inline-block; padding:0.2rem 0.6rem; margin:0.2rem; border-radius:4px; background:#f0ede8; font-size:0.8rem; }
.prompt-box { background:#f5f4f2; padding:1rem; border-radius:6px; font-size:0.85rem; line-height:1.5; margin-top:1rem; white-space:pre-wrap; }
.prompt-label { font-size:0.75rem; color:#8b7355; font-weight:500; margin-bottom:0.25rem; }
  ${paletteCss}
</style></head>
<body>
<section class="hero"><h1>${data.productName}</h1></section>
<div class="content">
<div class="grid">
  <div class="detail-card">
    <h3>产品信息</h3>
    <p><strong>SKU:</strong> ${data.sku}</p>
    <p><strong>品类:</strong> ${data.category}</p>
    <p><strong>材质:</strong> ${data.material}</p>
    <p><strong>风格:</strong> ${data.style}</p>
    <p><strong>场景:</strong> ${data.scene}</p>
    <div class="palette">${data.palette.map((c,i) => `<div class="swatch swatch-${i}" title="${c}"></div>`).join('')}</div>
    <div><span class="score ${data.brandScore >= 0.7 ? 'score-high' : data.brandScore >= 0.4 ? 'score-mid' : 'score-low'}">品牌匹配度: ${(data.brandScore*100).toFixed(0)}%</span></div>
  </div>
  <div class="detail-card">
    <h3>色彩</h3>
    ${data.colors.map(c => `<span class="tag">${c}</span>`).join('')}
    <h3 style="margin-top:1.5rem">材质故事</h3>
    <p style="line-height:1.8;color:#666">精选${data.material}材质，延续北欧设计传统，注重自然质感与手工工艺的融合。每一处细节都体现 NORHOR 对品质的坚持。</p>
  </div>
</div>
<div class="detail-card" style="margin-top:2rem">
  <h3>生成配置</h3>
  <div class="prompt-label">Product Prompt</div>
  <div class="prompt-box">${data.prompts}</div>
</div>
</div>
</body></html>`;
}
