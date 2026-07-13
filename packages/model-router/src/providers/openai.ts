// SPDX-License-Identifier: MIT

import { BaseProvider } from './base';
import type { ModelCapability } from '../types';

export class OpenAIProvider extends BaseProvider {
  readonly name = 'openai';

  defaultBaseUrl(): string {
    return 'https://api.openai.com/v1';
  }

  supports(capability: ModelCapability): boolean {
    return ['text', 'vision', 'code', 'reasoning', 'embedding'].includes(capability);
  }

  async complete(
    prompt: string,
    model: string,
    options?: Record<string, unknown>,
  ): Promise<{ content: string; usage: { promptTokens: number; completionTokens: number; totalTokens: number } }> {
    const result = await this.request('/chat/completions', {
      model: model ?? 'gpt-4o',
      messages: [{ role: 'user', content: prompt }],
      ...options,
    }) as any;
    const choice = result.choices?.[0];
    return {
      content: choice?.message?.content ?? '',
      usage: result.usage
        ? { promptTokens: result.usage.prompt_tokens, completionTokens: result.usage.completion_tokens, totalTokens: result.usage.total_tokens }
        : { promptTokens: 0, completionTokens: 0, totalTokens: 0 },
    };
  }

  async embed(text: string, model: string = 'text-embedding-3-small'): Promise<number[]> {
    const result = await this.request('/embeddings', {
      model,
      input: text,
    }) as any;
    return result.data?.[0]?.embedding ?? [];
  }
}
