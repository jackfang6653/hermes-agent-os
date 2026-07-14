// SPDX-License-Identifier: MIT

export interface MemoryEntry {
  id: string;
  key: string;
  value: unknown;
  type: MemoryType;
  tags: string[];
  source: string;
  ttl?: number;
  createdAt: number;
  updatedAt: number;
  expiresAt?: number;
}

export type MemoryType = 'session' | 'persistent' | 'knowledge' | 'checkpoint' | 'cache';

export interface MemoryQuery {
  key?: string;
  type?: MemoryType;
  tags?: string[];
  source?: string;
  limit?: number;
  offset?: number;
}

export interface MemoryStoreConfig {
  maxEntries: number;
  defaultTTL: number;
  persistPath: string;
  autoCleanup: boolean;
  cleanupInterval: number;
}

export interface Checkpoint {
  id: string;
  label: string;
  data: Record<string, unknown>;
  timestamp: number;
  version: number;
  tags: string[];
}

export interface RetentionPolicy {
  maxAge: number;
  maxEntriesPerType: number;
  priorityTags: string[];
}
