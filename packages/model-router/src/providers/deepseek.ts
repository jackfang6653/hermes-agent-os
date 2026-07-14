// SPDX-License-Identifier: MIT

import { BaseProvider } from './base.js';
import type { ModelCapability } from '../types.js';

export class DeepSeekProvider extends BaseProvider {
  readonly name = 'deepseek';

  defaultBaseUrl(): string {
    return 'https://api.deepseek.com/v1';
  }

  supports(capability: ModelCapability): boolean {
    return ['text', 'code', 'reasoning'].includes(capability);
  }

  async complete(
    prompt: string,
    model: string,
    options?: Record<string, unknown>,
  ): Promise<{ content: string; usage: { promptTokens: number; completionTokens: number; totalTokens: number } }> {
    const result = await this.request('/chat/completions', {
      model: model ?? 'deepseek-chat',
      messages: [{ role: 'user', content: prompt }],
      ...options,
    }) as any;
    const choice = result.choices?.[0];
    return {
      content: choice?.message?.content ?? '',
      usage: result.usage ?? { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 },
    };
  }

  async embed(_text: string, _model: string): Promise<number[]> {
    throw new Error('DeepSeek does not support embeddings');
  }
}
