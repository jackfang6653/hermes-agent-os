// SPDX-License-Identifier: MIT

export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  permissions: string[];
  profile: UserProfile;
  settings: UserSettings;
  isActive: boolean;
  lastLogin?: string;
  createdAt: string;
}

export type UserRole = 'admin' | 'designer' | 'reviewer' | 'viewer' | 'api';

export interface UserProfile {
  displayName: string;
  avatar?: string;
  department?: string;
  brandAccess: string[];
}

export interface UserSettings {
  theme: 'light' | 'dark' | 'system';
  language: string;
  notifications: boolean;
  defaultExportFormat: string;
}
