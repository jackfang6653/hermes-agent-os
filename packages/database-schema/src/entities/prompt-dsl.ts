// SPDX-License-Identifier: MIT

export interface PromptDSL {
  id: string;
  name: string;
  version: string;
  category: 'product' | 'scene' | 'camera' | 'lighting' | 'combined';
  template: string;
  variables: PromptVariable[];
  constraints: PromptConstraint[];
  negativePrompt: string;
  modelHints: ModelHint[];
}

export interface PromptVariable {
  name: string;
  type: 'string' | 'number' | 'enum';
  description: string;
  required: boolean;
  defaultValue?: string;
  options?: string[];
}

export interface PromptConstraint {
  type: 'format' | 'style' | 'color' | 'composition' | 'quality';
  value: string;
  weight: 'must' | 'should' | 'avoid';
}

export interface ModelHint {
  model: string;
  parameters: Record<string, unknown>;
  weight: number;
}
