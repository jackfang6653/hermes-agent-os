// SPDX-License-Identifier: MIT

import type { Checkpoint } from './types';

export class CheckpointManager {
  private store = new Map<string, Checkpoint>();

  save(checkpoint: Checkpoint): void {
    this.store.set(checkpoint.workflowId, checkpoint);
  }

  get(workflowId: string): Checkpoint | undefined {
    return this.store.get(workflowId);
  }

  remove(workflowId: string): boolean {
    return this.store.delete(workflowId);
  }

  has(workflowId: string): boolean {
    return this.store.has(workflowId);
  }

  list(): string[] {
    return Array.from(this.store.keys());
  }

  clear(): void {
    this.store.clear();
  }
}
