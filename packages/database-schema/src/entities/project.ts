// SPDX-License-Identifier: MIT

export interface Project {
  id: string;
  name: string;
  brandId: string;
  description: string;
  status: ProjectStatus;
  products: string[];
  config: ProjectConfig;
  createdAt: string;
  updatedAt: string;
}

export type ProjectStatus = 'planning' | 'in_progress' | 'review' | 'completed' | 'archived';

export interface ProjectConfig {
  exportFormat: string[];
  qualityGate: boolean;
  autoReview: boolean;
  defaultScene: string;
  defaultCamera: string;
  webhookUrl?: string;
}
