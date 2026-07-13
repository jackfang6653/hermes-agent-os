// SPDX-License-Identifier: MIT

export interface Camera {
  id: string;
  name: string;
  brand: string;
  model: string;
  sensor: 'full_frame' | 'aps_c' | 'medium_format';
  focalLengths: number[];
  apertureRange: [number, number];
  presets: CameraPreset[];
}

export interface CameraPreset {
  name: string;
  focalLength: number;
  aperture: number;
  shutterSpeed: string;
  iso: number;
  description: string;
}
