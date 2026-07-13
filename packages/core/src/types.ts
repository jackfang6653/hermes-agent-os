// SPDX-License-Identifier: MIT

export type KernelState = 'init' | 'starting' | 'running' | 'stopping' | 'stopped' | 'error';

export interface KernelConfig {
  name: string;
  version: string;
  maxPlugins?: number;
  shutdownTimeout?: number;
  logLevel?: 'debug' | 'info' | 'warn' | 'error';
}

export interface KernelEvent {
  type: string;
  source: string;
  timestamp: number;
  data?: unknown;
}

export interface PluginInfo {
  id: string;
  name: string;
  version: string;
  enabled: boolean;
  hooks: LifecycleHook[];
}

export interface PluginManifest {
  id: string;
  name: string;
  version: string;
  description: string;
  dependencies: string[];
  hooks: LifecycleHook[];
}

export type LifecycleHook = 'onInit' | 'onStart' | 'onStop' | 'onError';

export interface LifecycleMethods {
  onInit?(): Promise<void>;
  onStart?(): Promise<void>;
  onStop?(): Promise<void>;
  onError?(error: Error): Promise<void>;
}

export type KernelEventCallback = (event: KernelEvent) => void;
