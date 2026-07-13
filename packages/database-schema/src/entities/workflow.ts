// SPDX-License-Identifier: MIT

export interface Workflow {
  id: string;
  name: string;
  description: string;
  brandId?: string;
  version: string;
  steps: WorkflowStep[];
  triggers: WorkflowTrigger[];
  errorHandling: ErrorHandling;
  status: 'active' | 'draft' | 'paused' | 'archived';
}

export interface WorkflowStep {
  id: string;
  name: string;
  type: 'analyze' | 'generate' | 'transform' | 'validate' | 'export' | 'notify';
  config: Record<string, unknown>;
  dependsOn: string[];
  timeout: number;
  retry: RetryConfig;
}

export interface RetryConfig {
  maxAttempts: number;
  delay: number;
  backoff: 'linear' | 'exponential';
}

export interface WorkflowTrigger {
  type: 'manual' | 'webhook' | 'scheduled' | 'event';
  config: Record<string, unknown>;
}

export interface ErrorHandling {
  onError: 'abort' | 'skip' | 'retry' | 'fallback';
  fallbackStep?: string;
  notifyOnFail: boolean;
}
