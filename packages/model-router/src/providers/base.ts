// SPDX-License-Identifier: MIT

import type { ModelCapability } from '../types.js';

export abstract class BaseProvider {
  abstract readonly name: string;
  protected apiKey: string;
  protected baseUrl: string;

  constructor(config: { apiKey: string; baseUrl?: string }) {
    this.apiKey = config.apiKey;
    this.baseUrl = config.baseUrl ?? this.defaultBaseUrl();
  }

  abstract defaultBaseUrl(): string;
  abstract supports(capability: ModelCapability): boolean;

  abstract complete(
    prompt: string,
    model: string,
    options?: Record<string, unknown>,
  ): Promise<{
    content: string;
    usage: { promptTokens: number; completionTokens: number; totalTokens: number };
  }>;

  abstract embed(text: string, model: string): Promise<number[]>;

  protected async request(
    endpoint: string,
    body: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    const res = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      throw new Error(`Provider ${this.name} error ${res.status}: ${await res.text()}`);
    }
    return res.json() as Promise<Record<string, unknown>>;
  }
}
