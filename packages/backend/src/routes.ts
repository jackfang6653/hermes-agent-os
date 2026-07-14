// SPDX-License-Identifier: MIT

import type { RouteDef } from './types';

export const ROUTES: RouteDef[] = [
  // Health
  { method: 'GET', path: '/health', handler: 'healthCheck', auth: false, description: 'Health check' },

  // Projects
  { method: 'GET', path: '/api/projects', handler: 'listProjects', auth: true, description: 'List all projects' },
  { method: 'POST', path: '/api/projects', handler: 'createProject', auth: true, description: 'Create project' },
  { method: 'GET', path: '/api/projects/:id', handler: 'getProject', auth: true, description: 'Get project by ID' },
  { method: 'PUT', path: '/api/projects/:id', handler: 'updateProject', auth: true, description: 'Update project' },
  { method: 'DELETE', path: '/api/projects/:id', handler: 'deleteProject', auth: true, description: 'Delete project' },

  // Brands
  { method: 'GET', path: '/api/brands', handler: 'listBrands', auth: false, description: 'List brands' },
  { method: 'GET', path: '/api/brands/:id', handler: 'getBrand', auth: false, description: 'Get brand by ID' },
  { method: 'POST', path: '/api/brands', handler: 'createBrand', auth: true, description: 'Create brand' },

  // Workflows
  { method: 'GET', path: '/api/workflows', handler: 'listWorkflows', auth: true, description: 'List workflows' },
  { method: 'POST', path: '/api/workflows/:id/start', handler: 'startWorkflow', auth: true, description: 'Start workflow execution' },
  { method: 'POST', path: '/api/workflows/:id/stop', handler: 'stopWorkflow', auth: true, description: 'Stop workflow' },

  // Generation
  { method: 'POST', path: '/api/generate/product', handler: 'generateProductImage', auth: true, description: 'Generate product image' },
  { method: 'POST', path: '/api/generate/scene', handler: 'generateSceneImage', auth: true, description: 'Generate scene image' },

  // Export
  { method: 'POST', path: '/api/export', handler: 'exportProject', auth: true, description: 'Export project' },
  { method: 'GET', path: '/api/export/formats', handler: 'listExportFormats', auth: false, description: 'List export formats' },

  // Assets
  { method: 'POST', path: '/api/assets/upload', handler: 'uploadAsset', auth: true, description: 'Upload asset' },
  { method: 'GET', path: '/api/assets', handler: 'listAssets', auth: true, description: 'List assets' },
];

export function findRouteDef(method: string, path: string): RouteDef | undefined {
  return ROUTES.find(r => {
    if (r.method !== method) return false;
    const pattern = r.path.replace(/:id/g, '[^/]+').replace(/:([^/]+)/g, '[^/]+');
    return new RegExp(`^${pattern}$`).test(path);
  });
}
