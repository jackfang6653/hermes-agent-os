// SPDX-License-Identifier: MIT

import { EventEmitter } from 'events';
import type { KernelEvent, KernelEventCallback } from './types.js';

export class EventBus {
  private emitter = new EventEmitter();
  private history: KernelEvent[] = [];
  private readonly maxHistory: number;

  constructor(maxHistory = 500) {
    this.maxHistory = maxHistory;
    this.emitter.setMaxListeners(200);
  }

  emit(event: KernelEvent): void {
    this.history.push(event);
    if (this.history.length > this.maxHistory) {
      this.history.shift();
    }
    this.emitter.emit(event.type, event);
    this.emitter.emit('*', event);
  }

  on(type: string, callback: KernelEventCallback): void {
    this.emitter.on(type, callback);
  }

  off(type: string, callback: KernelEventCallback): void {
    this.emitter.off(type, callback);
  }

  once(type: string, callback: KernelEventCallback): void {
    this.emitter.once(type, callback);
  }

  getHistory(type?: string): KernelEvent[] {
    if (!type) return [...this.history];
    return this.history.filter(e => e.type === type);
  }

  clear(): void {
    this.history = [];
  }

  listenerCount(type: string): number {
    return this.emitter.listenerCount(type);
  }
}
