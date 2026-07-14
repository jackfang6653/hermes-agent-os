// SPDX-License-Identifier: MIT

import type { ApiRequest, ApiResponse } from './types';

export async function healthCheck(_req: ApiRequest<void>): Promise<ApiResponse<{ status: string; version: string }>> {
  return {
    status: 200,
    data: { status: 'ok', version: '1.0.0' },
    meta: { duration: 0 },
  };
}

export const handlers: Record<string, (req: any) => Promise<ApiResponse>> = {
  healthCheck,

  // Projects
  listProjects: async () => ({ status: 200, data: [], meta: { duration: 0 } }),
  createProject: async (req) => ({ status: 201, data: { id: 'new', ...req.body }, meta: { duration: 0 } }),
  getProject: async (req) => ({ status: 200, data: { id: req.params.id }, meta: { duration: 0 } }),
  updateProject: async (req) => ({ status: 200, data: { id: req.params.id, ...req.body }, meta: { duration: 0 } }),
  deleteProject: async (req) => ({ status: 200, data: { id: req.params.id, deleted: true }, meta: { duration: 0 } }),

  // Brands
  listBrands: async () => ({ status: 200, data: [], meta: { duration: 0 } }),
  getBrand: async (req) => ({ status: 200, data: { id: req.params.id }, meta: { duration: 0 } }),
  createBrand: async (req) => ({ status: 201, data: { id: 'new-brand', ...req.body }, meta: { duration: 0 } }),

  // Workflows
  listWorkflows: async () => ({ status: 200, data: [], meta: { duration: 0 } }),
  startWorkflow: async (req) => ({ status: 200, data: { workflowId: req.params.id, status: 'running' }, meta: { duration: 0 } }),
  stopWorkflow: async (req) => ({ status: 200, data: { workflowId: req.params.id, status: 'stopped' }, meta: { duration: 0 } }),

  // Generation
  generateProductImage: async () => ({ status: 200, data: { url: '', status: 'queued' }, meta: { duration: 0 } }),
  generateSceneImage: async () => ({ status: 200, data: { url: '', status: 'queued' }, meta: { duration: 0 } }),

  // Export
  exportProject: async () => ({ status: 200, data: { url: '', format: 'html' }, meta: { duration: 0 } }),
  listExportFormats: async () => ({ status: 200, data: ['html', 'pdf', 'zip', 'shopify'], meta: { duration: 0 } }),

  // Assets
  uploadAsset: async (req) => ({ status: 201, data: { id: 'new-asset', ...req.body }, meta: { duration: 0 } }),
  listAssets: async () => ({ status: 200, data: [], meta: { duration: 0 } }),
};
