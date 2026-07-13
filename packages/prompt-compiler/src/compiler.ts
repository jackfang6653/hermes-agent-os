// SPDX-License-Identifier: MIT

import type { PromptTemplate, PromptVariable, CompiledPrompt, CompilerConfig } from './types';

export class PromptCompiler {
  private templates: Map<string, PromptTemplate> = new Map();
  private config: CompilerConfig;

  constructor(config?: Partial<CompilerConfig>) {
    this.config = {
      maxLength: config?.maxLength ?? 4000,
      strictMode: config?.strictMode ?? true,
      defaultNegative: config?.defaultNegative ?? 'low quality, blurry, distorted, deformed, bad anatomy, watermark, text',
    };
  }

  register(template: PromptTemplate): void {
    this.templates.set(template.id, template);
  }

  getTemplate(id: string): PromptTemplate | undefined {
    return this.templates.get(id);
  }

  compile(templateId: string, variables: Record<string, string>): CompiledPrompt {
    const template = this.templates.get(templateId);
    if (!template) throw new Error(`Template '${templateId}' not found`);

    const warnings: string[] = [];

    // Validate required variables
    for (const v of template.variables) {
      if (v.required && !variables[v.name] && !v.defaultValue) {
        if (this.config.strictMode) {
          throw new Error(`Required variable '${v.name}' is missing`);
        }
        warnings.push(`Missing required variable: ${v.name}`);
      }
    }

    // Build variable map with defaults
    const resolved: Record<string, string> = {};
    for (const v of template.variables) {
      resolved[v.name] = variables[v.name] ?? v.defaultValue ?? '';
    }

    // Interpolate template
    let prompt = template.content;
    for (const [key, value] of Object.entries(resolved)) {
      prompt = prompt.replace(new RegExp(`\\{\\{\\s*${key}\\s*\\}\\}`, 'g'), value);
    }

    // Validate length
    if (prompt.length > this.config.maxLength) {
      warnings.push(`Prompt exceeds max length (${prompt.length} > ${this.config.maxLength})`);
    }

    return {
      prompt,
      negativePrompt: this.config.defaultNegative,
      variables: resolved,
      metadata: {
        templateId,
        compiledAt: Date.now(),
        warnings,
      },
    };
  }

  static simpleCompile(template: string, variables: Record<string, string | number>): string {
    let result = template;
    for (const [key, value] of Object.entries(variables)) {
      result = result.replace(new RegExp(`\\{\\{\\s*${key}\\s*\\}\\}`, 'g'), String(value));
    }
    return result;
  }
}
