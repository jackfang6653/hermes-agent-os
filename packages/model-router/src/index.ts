// SPDX-License-Identifier: MIT

export { ModelRouter } from './router';
export { BaseProvider } from './providers/base';
export { DeepSeekProvider } from './providers/deepseek';
export { OpenAIProvider } from './providers/openai';
export { selectModel, buildFallbackChain } from './policies/strategy';
export type {
  ModelProvider,
  ModelCapability,
  RouteConfig,
  RouteRequest,
  RouteResult,
  ProviderConfig,
  ModelInfo,
  RouteStrategy,
} from './types';
export const VERSION = '1.0.0';
