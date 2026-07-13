// SPDX-License-Identifier: MIT

export interface Scene {
  id: string;
  name: string;
  style: SceneStyle;
  description: string;
  lighting: LightingConfig;
  camera: CameraConfig;
  decoration: DecorationItem[];
  colorPalette: string[];
  moodKeywords: string[];
  referenceImages: string[];
}

export type SceneStyle = 'nordic_home' | 'modern_living' | 'boutique_space' | 'minimal' | 'wabi_sabi';

export interface LightingConfig {
  type: 'natural' | 'warm' | 'mixed' | 'studio' | 'dramatic';
  temperature: number;
  intensity: 'soft' | 'medium' | 'bright';
  direction: 'top' | 'side' | 'back' | 'diffuse';
}

export interface CameraConfig {
  angle: 'front' | 'three_quarter' | 'top_down' | 'eye_level' | 'macro';
  distance: 'close' | 'medium' | 'wide';
  lens: 'standard' | 'wide_angle' | 'macro';
  height: number;
}

export interface DecorationItem {
  type: string;
  style: string;
  color: string;
  placement: string;
}
