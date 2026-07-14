// SPDX-License-Identifier: MIT

export { PluginLoader } from './loader';
export { PluginMarketplace, BUILTIN_PLUGINS } from './marketplace';
export type {
  PluginManifest,
  PluginHook,
  PluginAPI,
  PluginLogger,
  PluginStorage,
  PluginEvents,
  PluginContext,
  MarketplaceEntry,
} from './types';
export const VERSION = '1.0.0';
