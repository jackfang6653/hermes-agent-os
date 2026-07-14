// SPDX-License-Identifier: MIT

export { NorhorPipeline } from './pipeline.js';
export { NORHOR_PROFILE, SCENE_PRESETS, PRODUCT_CATEGORIES } from './presets.js';
export { generateImage } from './image-gen.js';
export type { ImageGenResult, ImageGenConfig, ImageProvider } from './image-gen.js';
export type { GenerateOptions, ProductResult } from './pipeline.js';
export type { SceneId, CategoryId } from './presets.js';
export const VERSION = '1.0.0';
