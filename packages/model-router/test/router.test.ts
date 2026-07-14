// SPDX-License-Identifier: MIT
import { describe, it, expect } from 'vitest';
import { ModelRouter } from '../src/router.js';
import { selectModel, buildFallbackChain } from '../src/policies/strategy.js';
import type { RouteConfig, RouteRequest } from '../src/types.js';

describe('selectModel', () => {
  const configs: RouteConfig[] = [
    { provider: 'deepseek', model: 'deepseek-chat', priority: 1, cost: 0.5, capabilities: ['text', 'code'], fallbacks: ['gpt-4o'], maxRetries: 2, timeout: 30000 },
    { provider: 'openai', model: 'gpt-4o', priority: 2, cost: 5, capabilities: ['text', 'vision', 'code'], fallbacks: [], maxRetries: 2, timeout: 30000 },
    { provider: 'openai', model: 'gpt-4o-mini', priority: 3, cost: 0.15, capabilities: ['text'], fallbacks: [], maxRetries: 2, timeout: 30000 },
  ];

  it('should select cheapest model first', () => {
    const req: RouteRequest = { prompt: 'hello', capabilities: ['text'] };
    const result = selectModel(configs, req, 'cost_first');
    expect(result?.model).toBe('gpt-4o-mini'); // cheapest: 0.15
  });

  it('should prefer quality model', () => {
    const req: RouteRequest = { prompt: 'hello', capabilities: ['text'] };
    const result = selectModel(configs, req, 'quality_first');
    expect(result?.model).toBe('deepseek-chat'); // highest priority
  });

  it('should filter by capability', () => {
    const req: RouteRequest = { prompt: 'hello', capabilities: ['vision'] };
    const result = selectModel(configs, req);
    expect(result?.model).toBe('gpt-4o'); // only one with vision
  });

  it('should return null if no match', () => {
    const req: RouteRequest = { prompt: 'hello', capabilities: ['embedding'] as any };
    const result = selectModel(configs, req);
    expect(result).toBeNull();
  });
});

describe('buildFallbackChain', () => {
  it('should build fallback chain', () => {
    const configs: RouteConfig[] = [
      { provider: 'deepseek', model: 'deepseek-chat', priority: 1, cost: 0.5, capabilities: ['text'], fallbacks: ['gpt-4o'], maxRetries: 2, timeout: 30000 },
      { provider: 'openai', model: 'gpt-4o', priority: 2, cost: 5, capabilities: ['text'], fallbacks: [], maxRetries: 2, timeout: 30000 },
    ];
    const chain = buildFallbackChain(configs, configs[0]);
    expect(chain).toHaveLength(2);
    expect(chain[0].model).toBe('deepseek-chat');
    expect(chain[1].model).toBe('gpt-4o');
  });
});

describe('ModelRouter', () => {
  it('should configure and route', async () => {
    const router = new ModelRouter();
    router.configureProvider('deepseek', { apiKey: 'test-key' });
    router.addRouteConfig({
      provider: 'deepseek', model: 'deepseek-chat', priority: 1, cost: 0.5,
      capabilities: ['text', 'code'], fallbacks: [], maxRetries: 0, timeout: 5000,
    });

    await expect(
      router.route({ prompt: 'hi', capabilities: ['text'] }),
    ).rejects.toThrow(); // Will fail because API key is fake
  });

  it('should throw when no provider configured', async () => {
    const router = new ModelRouter();
    router.addRouteConfig({
      provider: 'deepseek', model: 'deepseek-chat', priority: 1, cost: 0.5,
      capabilities: ['text'], fallbacks: [], maxRetries: 0, timeout: 5000,
    });

    await expect(
      router.route({ prompt: 'hi', capabilities: ['text'] }),
    ).rejects.toThrow();
  });

  it('should throw on no matching model', async () => {
    const router = new ModelRouter();
    await expect(
      router.route({ prompt: 'hi', capabilities: ['vision'] }),
    ).rejects.toThrow('No suitable model found');
  });
});
