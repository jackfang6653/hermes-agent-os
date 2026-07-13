// SPDX-License-Identifier: MIT

import type { WorkflowDef, StepDef, WorkflowResult, StepResult, WorkflowStatus, Checkpoint, StepType } from './types';

type StepHandler = (step: StepDef, context: Record<string, unknown>) => Promise<Record<string, unknown>>;

export class WorkflowEngine {
  private workflows: Map<string, WorkflowDef> = new Map();
  private handlers: Map<StepType, StepHandler> = new Map();
  private checkpoints: Map<string, Checkpoint> = new Map();

  register(workflow: WorkflowDef): void {
    this.workflows.set(workflow.id, workflow);
  }

  registerHandler(type: StepType, handler: StepHandler): void {
    this.handlers.set(type, handler);
  }

  getWorkflow(id: string): WorkflowDef | undefined {
    return this.workflows.get(id);
  }

  async start(workflowId: string, initialContext: Record<string, unknown> = {}): Promise<WorkflowResult> {
    const workflow = this.workflows.get(workflowId);
    if (!workflow) throw new Error(`Workflow '${workflowId}' not found`);

    const stepResults: StepResult[] = [];
    const startTime = Date.now();
    const context = { ...initialContext };

    // Topological sort: resolve dependency order
    const executionOrder = this._resolveOrder(workflow.steps);

    for (const step of executionOrder) {
      // Check dependencies
      const depsSatisfied = step.dependsOn.every(depId =>
        stepResults.some(r => r.stepId === depId && r.status === 'success'),
      );

      if (!depsSatisfied) {
        stepResults.push({
          stepId: step.id,
          status: 'skipped',
          output: {},
          duration: 0,
          timestamp: Date.now(),
        });
        continue;
      }

      // Execute step
      const stepStart = Date.now();
      try {
        const handler = this.handlers.get(step.type);
        if (!handler) throw new Error(`No handler for step type: ${step.type}`);

        const output = await handler(step, context);
        context[step.id] = output;

        stepResults.push({
          stepId: step.id,
          status: 'success',
          output,
          duration: Date.now() - stepStart,
          timestamp: Date.now(),
        });

        // Save checkpoint after each successful step
        this._saveCheckpoint(workflowId, stepResults, context);
      } catch (err) {
        const error = String(err);

        if (workflow.onError === 'abort') {
          stepResults.push({
            stepId: step.id,
            status: 'failure',
            output: {},
            error,
            duration: Date.now() - stepStart,
            timestamp: Date.now(),
          });
          return {
            workflowId,
            status: 'failed',
            stepResults,
            totalDuration: Date.now() - startTime,
            error,
          };
        }

        if (workflow.onError === 'skip') {
          stepResults.push({
            stepId: step.id,
            status: 'skipped',
            output: {},
            error,
            duration: Date.now() - stepStart,
            timestamp: Date.now(),
          });
          continue;
        }

        // onError === 'retry'
        stepResults.push({
          stepId: step.id,
          status: 'failure',
          output: {},
          error,
          duration: Date.now() - stepStart,
          timestamp: Date.now(),
        });
        return {
          workflowId,
          status: 'failed',
          stepResults,
          totalDuration: Date.now() - startTime,
          error,
        };
      }
    }

    const allSuccess = stepResults.every(r => r.status === 'success' || r.status === 'skipped');
    return {
      workflowId,
      status: allSuccess ? 'completed' : 'failed',
      stepResults,
      totalDuration: Date.now() - startTime,
    };
  }

  getCheckpoint(workflowId: string): Checkpoint | undefined {
    return this.checkpoints.get(workflowId);
  }

  private _resolveOrder(steps: StepDef[]): StepDef[] {
    const visited = new Set<string>();
    const ordered: StepDef[] = [];
    const stepMap = new Map(steps.map(s => [s.id, s]));

    function visit(id: string) {
      if (visited.has(id)) return;
      visited.add(id);
      const step = stepMap.get(id);
      if (!step) return;
      for (const dep of step.dependsOn) {
        visit(dep);
      }
      ordered.push(step);
    }

    for (const step of steps) {
      visit(step.id);
    }

    return ordered;
  }

  private _saveCheckpoint(workflowId: string, stepResults: StepResult[], context: Record<string, unknown>): void {
    const cp = this.checkpoints.get(workflowId);
    this.checkpoints.set(workflowId, {
      id: `cp-${workflowId}-${(cp?.version ?? 0) + 1}`,
      workflowId,
      completedSteps: stepResults.filter(r => r.status === 'success').map(r => r.stepId),
      context,
      timestamp: Date.now(),
      version: (cp?.version ?? 0) + 1,
    });
  }
}
