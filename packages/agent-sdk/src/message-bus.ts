// SPDX-License-Identifier: MIT

import { EventEmitter } from 'events';
import type { Message, MessageHandler } from './types.js';

export class MessageBus {
  private emitter = new EventEmitter();
  private history: Message[] = [];
  private readonly maxHistory: number;

  constructor(maxHistory = 1000) {
    this.maxHistory = maxHistory;
    this.emitter.setMaxListeners(100);
  }

  async publish(message: Message): Promise<void> {
    this.history.push(message);
    if (this.history.length > this.maxHistory) {
      this.history.shift();
    }
    this.emitter.emit(message.type, message);
    this.emitter.emit('*', message);
  }

  subscribe(type: string, handler: MessageHandler): void {
    this.emitter.on(type, handler);
  }

  unsubscribe(type: string, handler: MessageHandler): void {
    this.emitter.off(type, handler);
  }

  subscribeOnce(type: string, handler: MessageHandler): void {
    this.emitter.once(type, handler);
  }

  getHistory(filter?: (m: Message) => boolean): Message[] {
    return filter ? this.history.filter(filter) : [...this.history];
  }

  clearHistory(): void {
    this.history = [];
  }

  listenerCount(type: string): number {
    return this.emitter.listenerCount(type);
  }

  removeAllListeners(type?: string): void {
    if (type) {
      this.emitter.removeAllListeners(type);
    } else {
      this.emitter.removeAllListeners();
    }
  }
}
