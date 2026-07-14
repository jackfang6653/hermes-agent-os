// SPDX-License-Identifier: MIT

export interface DesktopConfig {
  window: WindowConfig;
  theme: ThemeConfig;
  editor: EditorConfig;
  project: ProjectConfig;
}

export interface WindowConfig {
  title: string;
  width: number;
  height: number;
  minWidth: number;
  minHeight: number;
  frame: boolean;
  alwaysOnTop: boolean;
}

export interface ThemeConfig {
  mode: 'light' | 'dark' | 'system';
  primaryColor: string;
  fontFamily: string;
  borderRadius: number;
}

export interface EditorConfig {
  fontSize: number;
  lineHeight: number;
  wordWrap: boolean;
  tabSize: number;
  autoSave: boolean;
  autoSaveDelay: number;
}

export interface ProjectConfig {
  recentProjects: string[];
  defaultExportFormat: string;
  autoOpenLastProject: boolean;
}

export interface MainProcessAPI {
  getConfig(): Promise<DesktopConfig>;
  setConfig(config: Partial<DesktopConfig>): Promise<void>;
  openFileDialog(filters?: FileFilter[]): Promise<string[]>;
  saveFileDialog(defaultName: string): Promise<string | null>;
  openProject(path: string): Promise<ProjectInfo>;
  listRecentProjects(): Promise<string[]>;
  onMenuAction(callback: (action: string) => void): void;
}

export interface FileFilter {
  name: string;
  extensions: string[];
}

export interface ProjectInfo {
  id: string;
  name: string;
  path: string;
  brand: string;
  productCount: number;
  lastOpened: string;
}

export interface PageRoute {
  path: string;
  name: string;
  icon: string;
  component: string;
}
