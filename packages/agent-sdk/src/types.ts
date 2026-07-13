// SPDX-License-Identifier: MIT

export type AgentStatus = 'idle' | 'initializing' | 'running' | 'paused' | 'error' | 'stopped';

export interface AgentConfig {
  id: string;
  name: string;
  description?: string;
  capabilities: string[];
  maxRetries?: number;
  timeout?: number;
}

export interface AgentCapability {
  name: string;
  version: string;
  description: string;
  dependencies?: string[];
}

export interface AgentManifest {
  id: string;
  name: string;
  version: string;
  capabilities: AgentCapability[];
  dependencies: string[];
}

export interface Message {
  id: string;
  from: string;
  to: string;
  type: MessageType;
  payload: unknown;
  timestamp: number;
  correlationId?: string;
  replyTo?: string;
  ttl?: number;
}

export type MessageType =
  | 'request'
  | 'response'
  | 'event'
  | 'command'
  | 'error'
  | 'heartbeat';

export interface MessageHandler {
  (message: Message): Promise<Message | void>;
}

export interface RuntimeContext {
  agentId: string;
  config: Record<string, unknown>;
  memory: Map<string, unknown>;
  tools: Map<string, (...args: unknown[]) => Promise<unknown>>;
  get<T>(key: string): T | undefined;
  set<T>(key: string, value: T): void;
  executeTool(name: string, ...args: unknown[]): Promise<unknown>;
}
