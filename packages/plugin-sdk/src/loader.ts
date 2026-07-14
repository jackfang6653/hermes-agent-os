// SPDX-License-Identifier: MIT

import type { PluginManifest, PluginContext, PluginAPI, PluginLogger, PluginStorage, PluginEvents } from './types';

export class PluginLoader {
  private loaded: Map<string, PluginContext> = new Map();

  async load(manifest: PluginManifest): Promise<PluginContext> {
    if (this.loaded.has(manifest.id)) {
      throw new Error(`Plugin already loaded: ${manifest.id}`);
    }

    const logger: PluginLogger = {
      info: (msg) => console.log(`[${manifest.id}] ${msg}`),
      warn: (msg) => console.warn(`[${manifest.id}] ${msg}`),
      error: (msg) => console.error(`[${manifest.id}] ${msg}`),
      debug: (msg) => console.debug(`[${manifest.id}] ${msg}`),
    };

    const store = new Map<string, unknown>();
    const storage: PluginStorage = {
      get: async (key) => store.get(key),
      set: async (key, value) => { store.set(key, value); },
      delete: async (key) => store.delete(key),
      list: async () => Array.from(store.keys()),
    };

    const eventHandlers = new Map<string, Array<(data: unknown) => void>>();
    const events: PluginEvents = {
      emit: (event, data) => { eventHandlers.get(event)?.forEach(h => h(data)); },
      on: (event, handler) => {
        if (!eventHandlers.has(event)) eventHandlers.set(event, []);
        eventHandlers.get(event)!.push(handler);
      },
    };

    const api: PluginAPI = { config: {}, logger, storage, events };
    const context: PluginContext = {
      manifest,
      api,
      sandbox: {
        allowedPaths: manifest.permissions.filter(p => p.startsWith('path:')).map(p => p.slice(5)),
        allowedNetworks: manifest.permissions.filter(p => p.startsWith('network:')).map(p => p.slice(8)),
        maxMemory: 50 * 1024 * 1024, // 50 MB
        timeout: 30000,
      },
    };

    this.loaded.set(manifest.id, context);
    return context;
  }

  unload(pluginId: string): boolean {
    return this.loaded.delete(pluginId);
  }

  get(pluginId: string): PluginContext | undefined {
    return this.loaded.get(pluginId);
  }

  list(): PluginContext[] {
    return Array.from(this.loaded.values());
  }

  isLoaded(pluginId: string): boolean {
    return this.loaded.has(pluginId);
  }

  count(): number {
    return this.loaded.size;
  }
}
