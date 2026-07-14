// SPDX-License-Identifier: MIT

export { createDefaultConfig, mergeConfig } from './config';
export { ROUTES, SIDEBAR_ROUTES, findRoute } from './routes';
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
} from './types';
export const VERSION = '1.0.0';
