// SPDX-License-Identifier: MIT

import type { DesktopConfig, WindowConfig, ThemeConfig, EditorConfig } from './types';

export function createDefaultConfig(): DesktopConfig {
  return {
    window: {
      title: 'Hermes Agent OS',
      width: 1280,
      height: 800,
      minWidth: 900,
      minHeight: 600,
      frame: true,
      alwaysOnTop: false,
    },
    theme: {
      mode: 'dark',
      primaryColor: '#6366f1',
      fontFamily: "'Inter', 'Segoe UI', sans-serif",
      borderRadius: 8,
    },
    editor: {
      fontSize: 14,
      lineHeight: 1.6,
      wordWrap: true,
      tabSize: 2,
      autoSave: true,
      autoSaveDelay: 3000,
    },
    project: {
      recentProjects: [],
      defaultExportFormat: 'html',
      autoOpenLastProject: true,
    },
  };
}

export function mergeConfig(defaults: DesktopConfig, overrides: Partial<DesktopConfig>): DesktopConfig {
  return {
    window: { ...defaults.window, ...overrides.window },
    theme: { ...defaults.theme, ...overrides.theme },
    editor: { ...defaults.editor, ...overrides.editor },
    project: { ...defaults.project, ...overrides.project },
  };
}
