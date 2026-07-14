// SPDX-License-Identifier: MIT

import type { BrandProfile } from '@hermes-os/brand-engine';

export const NORHOR_PROFILE: BrandProfile = {
  id: 'norhor',
  name: 'NORHOR',
  slug: 'norhor',
  style: ['nordic', 'minimal', 'modern'],
  positioning: ['calm', 'warm', 'refined'],
  dna: {
    visual: { style: 'nordic', atmosphere: ['calm', 'warm', 'refined'], colorPalette: ['#f5f0e8', '#d4c5b0', '#8b7355'] },
    preserve: { productGeometry: true, materialTexture: true, colorAccuracy: true },
    variable: { camera: true, scene: true, composition: true },
  },
  grammar: {
    lighting: { preferred: ['natural', 'soft_diffuse', 'warm_ambient'], avoid: ['harsh_direct', 'fluorescent', 'colored_gel'], default: 'natural_side_lighting', temperature: [3500, 5500] },
    composition: { style: 'minimal_centered', productPosition: 'center', whitespace: 'ample', aspectRatio: '4:3' },
    color: { brandPalette: ['#f5f0e8', '#d4c5b0', '#8b7355', '#2c2c2c'], accentColors: ['#c4a882', '#e8d5c4'], avoidColors: ['#ff0000', '#00ff00'], saturation: [0.1, 0.4] },
  },
  constraints: [
    { field: 'style', rule: 'nordic|minimal|modern|scandinavian', severity: 'error', message: 'Style must match NORHOR brand identity' },
    { field: 'atmosphere', rule: 'calm|warm|refined|natural|cozy', severity: 'warn', message: 'Consider NORHOR brand atmosphere' },
  ],
};

export const SCENE_PRESETS = {
  nordic_living: {
    id: 'scene-nordic-living',
    name: '北欧客厅',
    style: 'nordic_home',
    lighting: { type: 'natural', temperature: 4500, intensity: 'soft', direction: 'diffuse' },
    camera: { angle: 'three_quarter', distance: 'medium', lens: 'standard', height: 120 },
    colorPalette: ['#f5f0e8', '#d4c5b0', '#8b7355'],
    moodKeywords: ['calm', 'warm', 'cozy'],
  },
  modern_dining: {
    id: 'scene-modern-dining',
    name: '现代餐厅',
    style: 'modern_living',
    lighting: { type: 'warm', temperature: 3500, intensity: 'medium', direction: 'top' },
    camera: { angle: 'eye_level', distance: 'medium', lens: 'standard', height: 150 },
    colorPalette: ['#2c2c2c', '#f5f0e8', '#c4a882'],
    moodKeywords: ['elegant', 'warm', 'sophisticated'],
  },
  boutique_studio: {
    id: 'scene-boutique',
    name: '精品展厅',
    style: 'boutique_space',
    lighting: { type: 'studio', temperature: 5000, intensity: 'bright', direction: 'side' },
    camera: { angle: 'front', distance: 'wide', lens: 'standard', height: 150 },
    colorPalette: ['#ffffff', '#d4c5b0', '#2c2c2c'],
    moodKeywords: ['clean', 'professional', 'premium'],
  },
} as const;

export const PRODUCT_CATEGORIES = [
  { id: 'sofa', name: '沙发', scenes: ['nordic_living', 'boutique_studio'] },
  { id: 'chair', name: '椅子', scenes: ['nordic_living', 'modern_dining'] },
  { id: 'table', name: '桌子', scenes: ['modern_dining', 'boutique_studio'] },
  { id: 'cabinet', name: '柜类', scenes: ['nordic_living', 'boutique_studio'] },
  { id: 'bed', name: '床', scenes: ['nordic_living'] },
  { id: 'lighting', name: '灯具', scenes: ['boutique_studio'] },
] as const;

export type SceneId = keyof typeof SCENE_PRESETS;
export type CategoryId = (typeof PRODUCT_CATEGORIES)[number]['id'];
