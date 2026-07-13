// SPDX-License-Identifier: MIT

export interface WorkflowDef {
  id: string;
  name: string;
  description: string;
  version: string;
  steps: StepDef[];
  onError: 'abort' | 'skip' | 'retry';
}

export interface StepDef {
  id: string;
  name: string;
  type: StepType;
  config: Record<string, unknown>;
  dependsOn: string[];
  timeout: number;
  retry: { maxAttempts: number; delay: number };
}

export type StepType =
  | 'analyze'
  | 'extract_dna'
  | 'create_scene'
  | 'compile_prompt'
  | 'generate_image'
  | 'qa_check'
  | 'export'
  | 'notify'
  | 'transform';

export type WorkflowStatus = 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';

export interface StepResult {
  stepId: string;
  status: 'success' | 'failure' | 'skipped';
  output: Record<string, unknown>;
  error?: string;
  duration: number;
  timestamp: number;
}

export interface WorkflowResult {
  workflowId: string;
  status: WorkflowStatus;
  stepResults: StepResult[];
  totalDuration: number;
  error?: string;
  checkpoint?: Checkpoint;
}

export interface Checkpoint {
  id: string;
  workflowId: string;
  completedSteps: string[];
  context: Record<string, unknown>;
  timestamp: number;
  version: number;
}
