// SPDX-License-Identifier: MIT

export { PluginLoader } from './loader.js';
export { PluginMarketplace, BUILTIN_PLUGINS } from './marketplace.js';
export type {
  PluginManifest,
  PluginHook,
  PluginAPI,
  PluginLogger,
  PluginStorage,
  PluginEvents,
  PluginContext,
  MarketplaceEntry,
} from './types.js';
export const VERSION = '1.0.0';
