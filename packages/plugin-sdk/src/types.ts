// SPDX-License-Identifier: MIT

export interface PluginManifest {
  id: string;
  name: string;
  version: string;
  description: string;
  author: string;
  license: string;
  entry: string;
  dependencies: string[];
  capabilities: string[];
  hooks: PluginHook[];
  permissions: string[];
  icon?: string;
  homepage?: string;
  repository?: string;
}

export type PluginHook =
  | 'onBeforeGenerate'
  | 'onAfterGenerate'
  | 'onBeforeExport'
  | 'onAfterExport'
  | 'onWorkflowStart'
  | 'onWorkflowEnd'
  | 'onBrandValidate'
  | 'onImageProcess';

export interface PluginAPI {
  config: Record<string, unknown>;
  logger: PluginLogger;
  storage: PluginStorage;
  events: PluginEvents;
}

export interface PluginLogger {
  info(msg: string): void;
  warn(msg: string): void;
  error(msg: string): void;
  debug(msg: string): void;
}

export interface PluginStorage {
  get(key: string): Promise<unknown>;
  set(key: string, value: unknown): Promise<void>;
  delete(key: string): Promise<boolean>;
  list(): Promise<string[]>;
}

export interface PluginEvents {
  emit(event: string, data: unknown): void;
  on(event: string, handler: (data: unknown) => void): void;
}

export interface PluginContext {
  manifest: PluginManifest;
  api: PluginAPI;
  sandbox: {
    allowedPaths: string[];
    allowedNetworks: string[];
    maxMemory: number;
    timeout: number;
  };
}

export interface MarketplaceEntry {
  pluginId: string;
  name: string;
  description: string;
  author: string;
  version: string;
  downloads: number;
  rating: number;
  verified: boolean;
  source: 'builtin' | 'npm' | 'registry';
}
