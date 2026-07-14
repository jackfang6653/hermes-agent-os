// SPDX-License-Identifier: MIT

import type { Checkpoint } from './types';
import { MemoryStore } from './store';

export class SnapshotManager {
  private checkpoints: Map<string, Checkpoint> = new Map();

  save(label: string, data: Record<string, unknown>, tags?: string[]): Checkpoint {
    const existing = this.checkpoints.get(label);
    const cp: Checkpoint = {
      id: `cp-${label}-${Date.now()}`,
      label,
      data,
      timestamp: Date.now(),
      version: (existing?.version ?? 0) + 1,
      tags: tags ?? [],
    };
    this.checkpoints.set(label, cp);
    return cp;
  }

  restore(label: string): Checkpoint | undefined {
    return this.checkpoints.get(label);
  }

  list(): Checkpoint[] {
    return Array.from(this.checkpoints.values())
      .sort((a, b) => b.timestamp - a.timestamp);
  }

  remove(label: string): boolean {
    return this.checkpoints.delete(label);
  }

  clear(): void {
    this.checkpoints.clear();
  }
}

export class RetentionManager {
  constructor(
    private store: MemoryStore,
    private config: {
      maxAge: number;
      maxEntriesPerType: number;
    },
  ) {}

  enforce(): number {
    let cleaned = 0;
    const types = ['session', 'persistent', 'knowledge', 'cache'] as const;

    for (const type of types) {
      const entries = this.store.query({ type, limit: Infinity as any });
      const sorted = entries.sort((a, b) => b.updatedAt - a.updatedAt);

      // Remove by age
      const cutoff = Date.now() - this.config.maxAge;
      for (const entry of sorted) {
        if (entry.updatedAt < cutoff) {
          this.store.delete(entry.key);
          cleaned++;
        }
      }

      // Remove by count
      while (sorted.length - cleaned > this.config.maxEntriesPerType) {
        const oldest = sorted[sorted.length - 1 - cleaned];
        this.store.delete(oldest.key);
        cleaned++;
      }
    }

    return cleaned;
  }
}
