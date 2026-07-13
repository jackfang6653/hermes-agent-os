// SPDX-License-Identifier: MIT

import type { KernelState, KernelConfig, KernelEvent, PluginInfo, PluginManifest, LifecycleMethods } from './types';
import { EventBus } from './event-bus';

export class Kernel {
  readonly eventBus: EventBus;
  private _state: KernelState = 'init';
  private plugins: Map<string, PluginInfo> = new Map();
  private instances: Map<string, LifecycleMethods> = new Map();
  private readonly config: Required<KernelConfig>;

  constructor(config: KernelConfig) {
    this.config = {
      name: config.name,
      version: config.version,
      maxPlugins: config.maxPlugins ?? 50,
      shutdownTimeout: config.shutdownTimeout ?? 30000,
      logLevel: config.logLevel ?? 'info',
    };
    this.eventBus = new EventBus();
  }

  get state(): KernelState {
    return this._state;
  }

  get pluginCount(): number {
    return this.plugins.size;
  }

  async start(): Promise<void> {
    if (this._state !== 'init') throw new Error(`Cannot start from state: ${this._state}`);
    this._state = 'starting';
    this._emit('kernel:starting', { name: this.config.name });

    for (const [id, instance] of this.instances) {
      if (instance.onStart) {
        try {
          await instance.onStart();
          const plugin = this.plugins.get(id)!;
          plugin.enabled = true;
        } catch (err) {
          this._emit('plugin:start-failed', { id, error: String(err) });
        }
      }
    }

    this._state = 'running';
    this._emit('kernel:started', { name: this.config.name });
  }

  async stop(): Promise<void> {
    if (this._state !== 'running') return;
    this._state = 'stopping';
    this._emit('kernel:stopping', {});

    const timeout = this.config.shutdownTimeout;
    const stopPromises = Array.from(this.instances.entries()).map(async ([id, instance]) => {
      if (instance.onStop) {
        await Promise.race([
          instance.onStop(),
          new Promise((_, reject) => setTimeout(() => reject(new Error(`Timeout stopping ${id}`)), timeout)),
        ]);
      }
    });

    await Promise.allSettled(stopPromises);
    this._state = 'stopped';
    this._emit('kernel:stopped', {});
  }

  loadPlugin(manifest: PluginManifest, instance: LifecycleMethods): boolean {
    if (this.plugins.size >= this.config.maxPlugins) {
      throw new Error(`Max plugins (${this.config.maxPlugins}) reached`);
    }
    if (this.plugins.has(manifest.id)) {
      return false;
    }

    const plugin: PluginInfo = {
      id: manifest.id,
      name: manifest.name,
      version: manifest.version,
      enabled: false,
      hooks: manifest.hooks,
    };

    this.plugins.set(manifest.id, plugin);
    this.instances.set(manifest.id, instance);

    if (instance.onInit) {
      instance.onInit().catch(err => {
        this._emit('plugin:init-failed', { id: manifest.id, error: String(err) });
      });
    }

    this._emit('plugin:loaded', { id: manifest.id, name: manifest.name });
    return true;
  }

  unloadPlugin(id: string): boolean {
    const instance = this.instances.get(id);
    if (instance?.onStop) {
      instance.onStop().catch(() => {});
    }
    this.plugins.delete(id);
    this.instances.delete(id);
    this._emit('plugin:unloaded', { id });
    return true;
  }

  hasPlugin(id: string): boolean {
    return this.plugins.has(id);
  }

  getPlugin(id: string): PluginInfo | undefined {
    return this.plugins.get(id);
  }

  listPlugins(): PluginInfo[] {
    return Array.from(this.plugins.values());
  }

  handleError(error: Error): void {
    this._emit('kernel:error', { message: error.message, stack: error.stack });
    for (const [id, instance] of this.instances) {
      if (instance.onError) {
        instance.onError(error).catch(() => {});
      }
    }
  }

  private _emit(type: string, data?: Record<string, unknown>): void {
    this.eventBus.emit({
      type,
      source: `kernel:${this.config.name}`,
      timestamp: Date.now(),
      data,
    });
  }
}
