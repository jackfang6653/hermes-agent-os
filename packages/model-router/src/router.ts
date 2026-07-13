// SPDX-License-Identifier: MIT

import type { RouteConfig, RouteRequest, RouteResult, ModelProvider } from './types';
import { selectModel, buildFallbackChain } from './policies/strategy';
import { BaseProvider } from './providers/base';
import { DeepSeekProvider } from './providers/deepseek';
import { OpenAIProvider } from './providers/openai';

type ProviderFactory = (config: { apiKey: string; baseUrl?: string }) => BaseProvider;

export class ModelRouter {
  private routeConfigs: RouteConfig[] = [];
  private providers: Map<ModelProvider, BaseProvider> = new Map();
  private providerFactories: Map<ModelProvider, ProviderFactory> = new Map();

  constructor() {
    this.registerProvider('deepseek', (c) => new DeepSeekProvider(c));
    this.registerProvider('openai', (c) => new OpenAIProvider(c));
  }

  registerProvider(provider: ModelProvider, factory: ProviderFactory): void {
    this.providerFactories.set(provider, factory);
  }

  configureProvider(provider: ModelProvider, config: { apiKey: string; baseUrl?: string }): void {
    const factory = this.providerFactories.get(provider);
    if (!factory) throw new Error(`Unknown provider: ${provider}`);
    this.providers.set(provider, factory(config));
  }

  setRouteConfigs(configs: RouteConfig[]): void {
    this.routeConfigs = configs;
  }

  addRouteConfig(config: RouteConfig): void {
    this.routeConfigs.push(config);
  }

  async route(request: RouteRequest): Promise<RouteResult> {
    const startTime = Date.now();

    // 1. Select primary model
    const primary = selectModel(this.routeConfigs, request, 'cost_first');
    if (!primary) throw new Error('No suitable model found');

    // 2. Build fallback chain
    const chain = buildFallbackChain(this.routeConfigs, primary);

    // 3. Try each in chain
    for (const config of chain) {
      const provider = this.providers.get(config.provider);
      if (!provider) continue;
      if (request.capabilities.some(c => !provider.supports(c))) continue;

      for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
        try {
          const result = await provider.complete(request.prompt, config.model, {
            timeout: config.timeout,
            ...request.context,
          });

          return {
            provider: config.provider,
            model: config.model,
            content: result.content,
            usage: {
              promptTokens: result.usage.promptTokens,
              completionTokens: result.usage.completionTokens,
              totalTokens: result.usage.totalTokens,
            },
            latency: Date.now() - startTime,
            cost: this._calcCost(config, result.usage),
            cached: false,
          };
        } catch (err) {
          if (attempt === config.maxRetries) {
            console.warn(`[Router] ${config.provider}/${config.model} failed after ${config.maxRetries + 1} attempts`);
          } else {
            await new Promise(r => setTimeout(r, 1000 * Math.pow(2, attempt)));
          }
        }
      }
    }

    throw new Error('All providers failed');
  }

  private _calcCost(config: RouteConfig, usage: { promptTokens: number; completionTokens: number }): number {
    return usage.promptTokens * config.cost;
  }
}
