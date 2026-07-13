// SPDX-License-Identifier: MIT

export type RuleOperator = 'equals' | 'not_equals' | 'contains' | 'greater_than' | 'less_than' | 'in' | 'between';

export interface Rule {
  id: string;
  name: string;
  description: string;
  scope: 'brand' | 'product' | 'scene' | 'prompt' | 'export';
  conditions: RuleCondition[];
  actions: RuleAction[];
  priority: number;
  enabled: boolean;
}

export interface RuleCondition {
  field: string;
  operator: RuleOperator;
  value: unknown;
}

export interface RuleAction {
  type: 'set' | 'override' | 'reject' | 'warn' | 'suggest';
  field: string;
  value: unknown;
  message?: string;
}
