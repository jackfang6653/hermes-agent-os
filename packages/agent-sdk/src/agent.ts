// SPDX-License-Identifier: MIT

import type { AgentConfig, AgentStatus, AgentCapability, Message, MessageHandler } from './types';

export abstract class Agent {
  readonly id: string;
  readonly name: string;
  readonly capabilities: AgentCapability[] = [];
  protected config: AgentConfig;
  protected status: AgentStatus = 'idle';
  protected handlers: Map<string, MessageHandler> = new Map();
  protected startTime?: number;

  constructor(config: AgentConfig) {
    this.id = config.id;
    this.name = config.name;
    this.config = config;
  }

  getStatus(): AgentStatus {
    return this.status;
  }

  getUptime(): number {
    return this.startTime ? Date.now() - this.startTime : 0;
  }

  async start(): Promise<void> {
    if (this.status === 'running') return;
    this.status = 'initializing';
    await this.onInit();
    this.status = 'running';
    this.startTime = Date.now();
  }

  async stop(): Promise<void> {
    if (this.status === 'stopped') return;
    await this.onStop();
    this.status = 'stopped';
    this.startTime = undefined;
  }

  async pause(): Promise<void> {
    if (this.status !== 'running') return;
    await this.onPause();
    this.status = 'paused';
  }

  async resume(): Promise<void> {
    if (this.status !== 'paused') return;
    this.status = 'running';
  }

  async handleMessage(message: Message): Promise<Message | void> {
    const handler = this.handlers.get(message.type);
    if (handler) {
      return handler.call(this, message);
    }
    // Fallback to generic handler
    return this.onMessage(message);
  }

  registerHandler(type: string, handler: MessageHandler): void {
    this.handlers.set(type, handler);
  }

  unregisterHandler(type: string): void {
    this.handlers.delete(type);
  }

  setCapability(capability: AgentCapability): void {
    const existing = this.capabilities.findIndex(c => c.name === capability.name);
    if (existing >= 0) {
      this.capabilities[existing] = capability;
    } else {
      this.capabilities.push(capability);
    }
  }

  // Lifecycle hooks
  protected abstract onInit(): Promise<void>;
  protected abstract onStop(): Promise<void>;
  protected onPause(): Promise<void> {
    return Promise.resolve();
  }
  protected onMessage(_message: Message): Promise<Message | void> {
    return Promise.resolve();
  }
}
