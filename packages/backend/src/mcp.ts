// SPDX-License-Identifier: MIT

import type { MCPToolDef } from './types';

export const MCP_TOOLS: MCPToolDef[] = [
  {
    name: 'list_projects',
    description: 'List all projects in the workspace',
    parameters: { type: 'object', properties: {}, required: [] },
    handler: 'listProjects',
  },
  {
    name: 'create_project',
    description: 'Create a new project',
    parameters: {
      type: 'object',
      properties: {
        name: { type: 'string', description: 'Project name' },
        brandId: { type: 'string', description: 'Brand ID' },
      },
      required: ['name'],
    },
    handler: 'createProject',
  },
  {
    name: 'start_workflow',
    description: 'Start a workflow execution',
    parameters: {
      type: 'object',
      properties: {
        workflowId: { type: 'string', description: 'Workflow ID' },
        context: { type: 'object', description: 'Initial context' },
      },
      required: ['workflowId'],
    },
    handler: 'startWorkflow',
  },
  {
    name: 'generate_product_image',
    description: 'Generate a product image',
    parameters: {
      type: 'object',
      properties: {
        sku: { type: 'string', description: 'Product SKU' },
        style: { type: 'string', description: 'Image style' },
        scene: { type: 'string', description: 'Scene type' },
      },
      required: ['sku'],
    },
    handler: 'generateProductImage',
  },
  {
    name: 'export_project',
    description: 'Export a project to specified format',
    parameters: {
      type: 'object',
      properties: {
        projectId: { type: 'string', description: 'Project ID' },
        format: { type: 'string', enum: ['html', 'pdf', 'zip'], description: 'Export format' },
      },
      required: ['projectId', 'format'],
    },
    handler: 'exportProject',
  },
];
