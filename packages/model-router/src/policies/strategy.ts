// SPDX-License-Identifier: MIT

import type { RouteConfig, RouteRequest, RouteStrategy } from '../types';

export function selectModel(
  configs: RouteConfig[],
  request: RouteRequest,
  strategy: RouteStrategy = 'cost_first',
): RouteConfig | null {
  // Filter by required capabilities
  let candidates = configs.filter(c =>
    request.capabilities.every(cap => c.capabilities.includes(cap)),
  );

  if (candidates.length === 0) return null;

  // Filter by max cost
  if (request.maxCost) {
    candidates = candidates.filter(c => c.cost <= request.maxCost!);
  }

  // Filter by preferred provider
  if (request.preferredProvider) {
    const preferred = candidates.filter(c => c.provider === request.preferredProvider);
    if (preferred.length > 0) candidates = preferred;
  }

  // Sort by strategy
  switch (strategy) {
    case 'cost_first':
      candidates.sort((a, b) => a.cost - b.cost || a.priority - b.priority);
      break;
    case 'quality_first':
      candidates.sort((a, b) => a.priority - b.priority || a.cost - b.cost);
      break;
    case 'fallback':
      // Keep original order (fallback list order)
      break;
  }

  return candidates[0] ?? null;
}

export function buildFallbackChain(
  configs: RouteConfig[],
  primary: RouteConfig,
): RouteConfig[] {
  const chain: RouteConfig[] = [primary];
  for (const fallbackId of primary.fallbacks) {
    const fb = configs.find(c => c.model === fallbackId);
    if (fb && !chain.includes(fb)) {
      chain.push(fb);
    }
  }
  return chain;
}
