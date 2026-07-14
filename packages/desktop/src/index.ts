// SPDX-License-Identifier: MIT

export { createDefaultConfig, mergeConfig } from './config.js';
export { ROUTES, SIDEBAR_ROUTES, findRoute } from './routes.js';
export type {
  DesktopConfig,
  WindowConfig,
  ThemeConfig,
  EditorConfig,
  ProjectConfig,
  MainProcessAPI,
  FileFilter,
  ProjectInfo,
  PageRoute,
} from './types.js';
export const VERSION = '1.0.0';
