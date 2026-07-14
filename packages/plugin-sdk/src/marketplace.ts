// SPDX-License-Identifier: MIT

import type { MarketplaceEntry } from './types';

export const BUILTIN_PLUGINS: MarketplaceEntry[] = [
  {
    pluginId: 'norhor-brand',
    name: 'NORHOR Brand Kit',
    description: 'NORHOR brand compliance, DNA extraction, scene presets',
    author: 'Hermes OS',
    version: '1.0.0',
    downloads: 0,
    rating: 5,
    verified: true,
    source: 'builtin',
  },
  {
    pluginId: 'export-html',
    name: 'HTML Export',
    description: 'Export product detail pages as responsive HTML',
    author: 'Hermes OS',
    version: '1.0.0',
    downloads: 0,
    rating: 5,
    verified: true,
    source: 'builtin',
  },
  {
    pluginId: 'vision-gpt4o',
    name: 'GPT-4o Vision Connector',
    description: 'Connect to OpenAI GPT-4o for product and scene analysis',
    author: 'Hermes OS',
    version: '1.0.0',
    downloads: 0,
    rating: 5,
    verified: true,
    source: 'builtin',
  },
];

export class PluginMarketplace {
  private entries: Map<string, MarketplaceEntry> = new Map();

  constructor() {
    for (const p of BUILTIN_PLUGINS) {
      this.entries.set(p.pluginId, p);
    }
  }

  register(entry: MarketplaceEntry): void {
    this.entries.set(entry.pluginId, entry);
  }

  get(pluginId: string): MarketplaceEntry | undefined {
    return this.entries.get(pluginId);
  }

  search(query: string): MarketplaceEntry[] {
    const lower = query.toLowerCase();
    return Array.from(this.entries.values()).filter(
      e =>
        e.name.toLowerCase().includes(lower) ||
        e.description.toLowerCase().includes(lower) ||
        e.author.toLowerCase().includes(lower),
    );
  }

  list(): MarketplaceEntry[] {
    return Array.from(this.entries.values());
  }

  listBySource(source: MarketplaceEntry['source']): MarketplaceEntry[] {
    return Array.from(this.entries.values()).filter(e => e.source === source);
  }
}
