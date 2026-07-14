// SPDX-License-Identifier: MIT

import type { PromptTemplate } from '../types.js';

export const PRODUCT_PROMPT: PromptTemplate = {
  id: 'product-main',
  name: 'Product Main Image',
  content: `A {{style}} {{product_type}} photographed in {{lighting}} lighting,
{{camera_angle}} view, {{background}} background.
Product details: {{material}} construction, {{color}} colorway,
{{texture}} texture, {{craftsmanship}} craftsmanship.
Atmosphere: {{atmosphere}}.
Style: product photography, commercial, {{resolution}}.`,
  variables: [
    { name: 'style', type: 'string', description: 'Brand style', required: true },
    { name: 'product_type', type: 'string', description: 'Product category', required: true },
    { name: 'lighting', type: 'string', description: 'Lighting type', required: true, defaultValue: 'natural' },
    { name: 'camera_angle', type: 'string', description: 'Camera angle', required: true, defaultValue: 'three-quarter' },
    { name: 'background', type: 'string', description: 'Background style', required: false, defaultValue: 'neutral' },
    { name: 'material', type: 'string', description: 'Material', required: true },
    { name: 'color', type: 'string', description: 'Color', required: true },
    { name: 'texture', type: 'string', description: 'Texture', required: false, defaultValue: 'smooth' },
    { name: 'craftsmanship', type: 'string', description: 'Craftsmanship', required: false, defaultValue: 'refined' },
    { name: 'atmosphere', type: 'string', description: 'Atmosphere', required: false, defaultValue: 'calm' },
    { name: 'resolution', type: 'string', description: 'Resolution', required: false, defaultValue: '8K' },
  ],
  category: 'product',
  constraints: ['No watermark', 'Studio lighting'],
};

export const SCENE_PROMPT: PromptTemplate = {
  id: 'scene-lifestyle',
  name: 'Scene Lifestyle Image',
  content: `Interior design photography of a {{scene_style}} {{room_type}}.
 featuring {{product_type}} in {{product_color}}.
The space features {{lighting}} lighting with {{color_palette}} palette,
{{decoration_style}} decor, {{atmosphere}} atmosphere.
Composition: {{composition}}.
Style: interior photography, editorial, {{resolution}}.`,
  variables: [
    { name: 'scene_style', type: 'string', description: 'Scene style', required: true },
    { name: 'room_type', type: 'string', description: 'Room type', required: true, defaultValue: 'living room' },
    { name: 'product_type', type: 'string', description: 'Product in scene', required: true },
    { name: 'product_color', type: 'string', description: 'Product color', required: true },
    { name: 'lighting', type: 'string', description: 'Lighting', required: true, defaultValue: 'warm natural' },
    { name: 'color_palette', type: 'string', description: 'Color palette', required: true },
    { name: 'decoration_style', type: 'string', description: 'Decor style', required: false, defaultValue: 'minimal' },
    { name: 'atmosphere', type: 'string', description: 'Atmosphere', required: false, defaultValue: 'cozy' },
    { name: 'composition', type: 'string', description: 'Composition style', required: false, defaultValue: 'balanced' },
    { name: 'resolution', type: 'string', description: 'Resolution', required: false, defaultValue: '8K' },
  ],
  category: 'scene',
  constraints: ['Natural light preferred', 'Brand color palette'],
};

export const DETAIL_PROMPT: PromptTemplate = {
  id: 'detail-story',
  name: 'Detail Page Story',
  content: `Product detail photography of {{product_type}} in {{style}} style.
Focus on {{feature_focus}}.
Material close-up: {{material}} -- emphasizing {{texture}} texture and {{craftsmanship}}.
Color: {{color}} on {{background}}.
Atmosphere: {{atmosphere}}.
Style: editorial product detail, macro detail, {{resolution}}.`,
  variables: [
    { name: 'product_type', type: 'string', description: 'Product', required: true },
    { name: 'style', type: 'string', description: 'Style', required: true },
    { name: 'feature_focus', type: 'string', description: 'Feature to highlight', required: true },
    { name: 'material', type: 'string', description: 'Material', required: true },
    { name: 'texture', type: 'string', description: 'Texture', required: true },
    { name: 'craftsmanship', type: 'string', description: 'Craftsmanship detail', required: false, defaultValue: 'refined' },
    { name: 'color', type: 'string', description: 'Color', required: true },
    { name: 'background', type: 'string', description: 'Background', required: false, defaultValue: 'neutral' },
    { name: 'atmosphere', type: 'string', description: 'Atmosphere', required: false, defaultValue: 'calm' },
    { name: 'resolution', type: 'string', description: 'Resolution', required: false, defaultValue: '8K' },
  ],
  category: 'detail',
  constraints: ['Macro lens', 'Material texture visible'],
};
