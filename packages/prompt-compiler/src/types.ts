// SPDX-License-Identifier: MIT

export interface PromptTemplate {
  id: string;
  name: string;
  content: string;
  variables: PromptVariable[];
  category: 'product' | 'scene' | 'detail';
  constraints: string[];
}

export interface PromptVariable {
  name: string;
  type: 'string' | 'number' | 'enum' | 'array';
  description: string;
  required: boolean;
  defaultValue?: string;
  options?: string[];
}

export interface CompiledPrompt {
  prompt: string;
  negativePrompt: string;
  variables: Record<string, string>;
  metadata: {
    templateId: string;
    compiledAt: number;
    warnings: string[];
  };
}

export interface CompilerConfig {
  maxLength: number;
  strictMode: boolean;
  defaultNegative: string;
}
