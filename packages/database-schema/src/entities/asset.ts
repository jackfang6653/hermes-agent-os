// SPDX-License-Identifier: MIT

export interface Asset {
  id: string;
  type: AssetType;
  name: string;
  url: string;
  localPath?: string;
  size: number;
  format: string;
  dimensions?: { width: number; height: number };
  duration?: number;
  tags: string[];
  metadata: Record<string, unknown>;
  projectId: string;
  status: 'uploading' | 'processing' | 'ready' | 'failed';
  createdAt: string;
  updatedAt: string;
}

export type AssetType = 'image' | 'video' | 'document' | 'model_3d' | 'audio' | 'other';
