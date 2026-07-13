// SPDX-License-Identifier: MIT

export type ModelProvider = 'deepseek' | 'openai' | 'doubao' | 'qwen' | 'gemini';
export type ModelCapability = 'text' | 'vision' | 'code' | 'reasoning' | 'embedding';

export interface RouteConfig {
  provider: ModelProvider;
  model: string;
  priority: number;
  cost: number;
  capabilities: ModelCapability[];
  fallbacks: string[];
  maxRetries: number;
  timeout: number;
}

export interface RouteRequest {
  prompt: string;
  capabilities: ModelCapability[];
  maxCost?: number;
  preferredProvider?: ModelProvider;
  context?: Record<string, unknown>;
}

export interface RouteResult {
  provider: ModelProvider;
  model: string;
  content: string;
  usage: { promptTokens: number; completionTokens: number; totalTokens: number };
  latency: number;
  cost: number;
  cached: boolean;
}

export interface ProviderConfig {
  apiKey: string;
  baseUrl?: string;
  defaultModel: string;
  models: Record<string, ModelInfo>;
}

export interface ModelInfo {
  name: string;
  capabilities: ModelCapability[];
  costPer1KInput: number;
  costPer1KOutput: number;
  maxTokens: number;
}

export type RouteStrategy = 'cost_first' | 'quality_first' | 'fallback';
