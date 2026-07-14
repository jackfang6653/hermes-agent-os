// SPDX-License-Identifier: MIT

import type { MemoryEntry, MemoryQuery, MemoryType } from './types';

export class MemoryStore {
  private entries: Map<string, MemoryEntry> = new Map();
  private maxEntries: number;

  constructor(maxEntries = 10000) {
    this.maxEntries = maxEntries;
  }

  set(key: string, value: unknown, options?: {
    type?: MemoryType;
    tags?: string[];
    source?: string;
    ttl?: number;
  }): MemoryEntry {
    const now = Date.now();
    const entry: MemoryEntry = {
      id: `mem-${key}-${now}`,
      key,
      value,
      type: options?.type ?? 'session',
      tags: options?.tags ?? [],
      source: options?.source ?? 'system',
      createdAt: now,
      updatedAt: now,
      expiresAt: options?.ttl ? now + options.ttl : undefined,
    };

    // Evict oldest if at capacity
    if (this.entries.size >= this.maxEntries) {
      const oldest = Array.from(this.entries.values())
        .sort((a, b) => a.createdAt - b.createdAt)[0];
      this.entries.delete(oldest.id);
    }

    this.entries.set(entry.id, entry);
    return entry;
  }

  get(key: string): MemoryEntry | undefined {
    const entries = this.query({ key });
    if (entries.length === 0) return undefined;
    const entry = entries[entries.length - 1]; // most recent
    // Check expiry
    if (entry.expiresAt && Date.now() > entry.expiresAt) {
      this.entries.delete(entry.id);
      return undefined;
    }
    return entry;
  }

  getValue<T>(key: string): T | undefined {
    return this.get(key)?.value as T | undefined;
  }

  delete(key: string): boolean {
    const entries = this.query({ key });
    let deleted = false;
    for (const e of entries) {
      if (this.entries.delete(e.id)) deleted = true;
    }
    return deleted;
  }

  query(query: MemoryQuery): MemoryEntry[] {
    let results = Array.from(this.entries.values());

    if (query.key) {
      results = results.filter(e => e.key === query.key);
    }
    if (query.type) {
      results = results.filter(e => e.type === query.type);
    }
    if (query.tags && query.tags.length > 0) {
      results = results.filter(e =>
        query.tags!.some(t => e.tags.includes(t)),
      );
    }
    if (query.source) {
      results = results.filter(e => e.source === query.source);
    }

    // Filter expired
    results = results.filter(e => !e.expiresAt || Date.now() <= e.expiresAt);

    // Sort by recency
    results.sort((a, b) => b.updatedAt - a.updatedAt);

    // Pagination
    const offset = query.offset ?? 0;
    const limit = query.limit ?? results.length;
    return results.slice(offset, offset + limit);
  }

  count(): number {
    return this.entries.size;
  }

  clear(): void {
    this.entries.clear();
  }

  cleanup(): number {
    const now = Date.now();
    let removed = 0;
    for (const [id, entry] of Array.from(this.entries)) {
      if (entry.expiresAt && now > entry.expiresAt) {
        this.entries.delete(id);
        removed++;
      }
    }
    return removed;
  }

  toJSON(): Record<string, unknown> {
    return {
      size: this.entries.size,
      maxEntries: this.maxEntries,
      entries: Array.from(this.entries.values()),
    };
  }
}
