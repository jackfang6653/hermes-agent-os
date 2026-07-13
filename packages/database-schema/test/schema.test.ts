// SPDX-License-Identifier: MIT
import { describe, it, expect } from 'vitest';
import type {
  Brand, Category, Product, SKU, Scene,
  Material, User, Project, Workflow,
} from '../src/entities';

describe('Database Schema Types', () => {
  it('Brand should validate structure', () => {
    const brand: Brand = {
      id: 'b1', name: 'NORHOR', slug: 'norhor',
      category: 'furniture', style: ['nordic'],
      positioning: ['modern'],
      dna: {
        visual: { style: 'nordic', atmosphere: ['calm'], colorPalette: ['#f5f0e8'] },
        preserve: { productGeometry: true, materialTexture: true, colorAccuracy: true },
        variable: { camera: true, scene: true, composition: true },
      },
      createdAt: '2024-01-01', updatedAt: '2024-01-01',
    };
    expect(brand.name).toBe('NORHOR');
    expect(brand.dna.visual.style).toBe('nordic');
  });

  it('Product should validate dimensions', () => {
    const product: Product = {
      id: 'p1', sku: 'CS-001', name: 'Cloud Sofa',
      brandId: 'b1', categoryId: 'c1',
      description: 'A comfortable sofa', dimensions: { width: 200, height: 80, depth: 70, unit: 'cm' },
      materials: [{ name: 'Linen', type: 'fabric' }],
      color: { name: 'Beige', hex: '#f5f0e8', family: 'neutral' },
      texture: 'smooth', craftsmanship: 'handcrafted',
      images: [], tags: [], status: 'active',
      fixedParameters: {}, variableParameters: {},
      createdAt: '2024-01-01', updatedAt: '2024-01-01',
    };
    expect(product.dimensions.width).toBe(200);
    expect(product.materials[0].name).toBe('Linen');
  });

  it('Scene should have valid style', () => {
    const scene: Scene = {
      id: 's1', name: 'Nordic Living', style: 'nordic_home',
      description: 'Cozy nordic living room',
      lighting: { type: 'natural', temperature: 5000, intensity: 'soft', direction: 'diffuse' },
      camera: { angle: 'three_quarter', distance: 'medium', lens: 'standard', height: 120 },
      decoration: [], colorPalette: ['#f5f0e8', '#d4c5b0'],
      moodKeywords: ['calm', 'warm'], referenceImages: [],
    };
    expect(scene.style).toBe('nordic_home');
    expect(scene.lighting.type).toBe('natural');
  });

  it('User should support roles', () => {
    const admin: User = {
      id: 'u1', username: 'admin', email: 'admin@norhor.com',
      role: 'admin', permissions: ['*'],
      profile: { displayName: 'Admin', brandAccess: ['norhor'] },
      settings: { theme: 'dark', language: 'zh', notifications: true, defaultExportFormat: 'html' },
      isActive: true, createdAt: '2024-01-01',
    };
    expect(admin.role).toBe('admin');
    expect(admin.settings.theme).toBe('dark');
  });

  it('Workflow should handle error strategies', () => {
    const workflow: Workflow = {
      id: 'w1', name: 'NORHOR Detail Gen', description: '',
      version: '1.0',
      steps: [{
        id: 'step1', name: 'Analyze', type: 'analyze',
        config: {}, dependsOn: [], timeout: 300,
        retry: { maxAttempts: 3, delay: 1, backoff: 'exponential' },
      }],
      triggers: [{ type: 'manual', config: {} }],
      errorHandling: { onError: 'fallback', notifyOnFail: true },
      status: 'active',
    };
    expect(workflow.steps[0].retry.backoff).toBe('exponential');
    expect(workflow.errorHandling.onError).toBe('fallback');
  });
});
