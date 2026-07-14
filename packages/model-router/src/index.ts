// SPDX-License-Identifier: MIT

export { ModelRouter } from './router.js';
export { BaseProvider } from './providers/base.js';
export { DeepSeekProvider } from './providers/deepseek.js';
export { OpenAIProvider } from './providers/openai.js';
export { selectModel, buildFallbackChain } from './policies/strategy.js';
export type {
  ModelProvider,
  ModelCapability,
  RouteConfig,
  RouteRequest,
  RouteResult,
  ProviderConfig,
  ModelInfo,
  RouteStrategy,
} from './types.js';
export const VERSION = '1.0.0';
