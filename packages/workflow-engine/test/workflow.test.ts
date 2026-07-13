// SPDX-License-Identifier: MIT
import { describe, it, expect } from 'vitest';
import { WorkflowEngine } from '../src/engine';
import { createNorhorPipeline } from '../src/pipeline';
import { CheckpointManager } from '../src/checkpoint';
import type { StepDef } from '../src/types';

describe('WorkflowEngine', () => {
  it('should execute a simple workflow', async () => {
    const engine = new WorkflowEngine();
    engine.registerHandler('analyze', async (step) => ({ result: 'analyzed' }));
    engine.registerHandler('export', async (step) => ({ result: 'exported' }));

    engine.register({
      id: 'simple', name: 'Simple', description: '', version: '1.0',
      steps: [
        { id: 's1', name: 'Analyze', type: 'analyze', config: {}, dependsOn: [], timeout: 5000, retry: { maxAttempts: 1, delay: 100 } },
        { id: 's2', name: 'Export', type: 'export', config: {}, dependsOn: ['s1'], timeout: 5000, retry: { maxAttempts: 1, delay: 100 } },
      ],
      onError: 'abort',
    });

    const result = await engine.start('simple');
    expect(result.status).toBe('completed');
    expect(result.stepResults).toHaveLength(2);
    expect(result.stepResults[0].status).toBe('success');
    expect(result.stepResults[1].status).toBe('success');
  });

  it('should handle step failure with abort', async () => {
    const engine = new WorkflowEngine();
    engine.registerHandler('analyze', async () => { throw new Error('Analysis failed'); });
    engine.registerHandler('export', async (step) => ({ result: 'done' }));

    engine.register({
      id: 'fail-test', name: 'Fail', description: '', version: '1.0',
      steps: [
        { id: 's1', name: 'Analyze', type: 'analyze', config: {}, dependsOn: [], timeout: 5000, retry: { maxAttempts: 1, delay: 100 } },
        { id: 's2', name: 'Export', type: 'export', config: {}, dependsOn: ['s1'], timeout: 5000, retry: { maxAttempts: 1, delay: 100 } },
      ],
      onError: 'abort',
    });

    const result = await engine.start('fail-test');
    expect(result.status).toBe('failed');
    expect(result.error).toContain('Analysis failed');
  });

  it('should skip failed step on skip mode', async () => {
    const engine = new WorkflowEngine();
    engine.registerHandler('analyze', async () => { throw new Error('fail'); });
    engine.registerHandler('export', async (step) => ({ result: 'done' }));

    engine.register({
      id: 'skip-test', name: 'Skip', description: '', version: '1.0',
      steps: [
        { id: 's1', name: 'Analyze', type: 'analyze', config: {}, dependsOn: [], timeout: 5000, retry: { maxAttempts: 1, delay: 100 } },
        { id: 's2', name: 'Export', type: 'export', config: {}, dependsOn: ['s1'], timeout: 5000, retry: { maxAttempts: 1, delay: 100 } },
      ],
      onError: 'skip',
    });

    const result = await engine.start('skip-test');
    // s2 depends on s1 which failed, so s2 is skipped
    expect(result.stepResults[1].status).toBe('skipped');
  });
});

describe('NORHOR Pipeline', () => {
  it('should create pipeline with 7 steps', () => {
    const pipeline = createNorhorPipeline();
    expect(pipeline.steps).toHaveLength(7);
    expect(pipeline.steps[0].id).toBe('analyze_product');
    expect(pipeline.steps[6].id).toBe('export');
  });

  it('should have correct dependency chain', () => {
    const pipeline = createNorhorPipeline();
    // Last step depends on QA
    const last = pipeline.steps[6];
    expect(last.dependsOn).toContain('qa_check');
    // QA depends on generate
    const qa = pipeline.steps[5];
    expect(qa.dependsOn).toContain('generate_image');
  });
});

describe('CheckpointManager', () => {
  it('should save and retrieve checkpoints', () => {
    const cm = new CheckpointManager();
    cm.save({ id: 'cp-1', workflowId: 'w1', completedSteps: ['s1'], context: {}, timestamp: Date.now(), version: 1 });
    expect(cm.has('w1')).toBe(true);
    const cp = cm.get('w1');
    expect(cp!.completedSteps).toContain('s1');
  });

  it('should remove checkpoints', () => {
    const cm = new CheckpointManager();
    cm.save({ id: 'cp-1', workflowId: 'w1', completedSteps: [], context: {}, timestamp: Date.now(), version: 1 });
    cm.remove('w1');
    expect(cm.has('w1')).toBe(false);
  });

  it('should list workflow IDs', () => {
    const cm = new CheckpointManager();
    cm.save({ id: 'cp-1', workflowId: 'w1', completedSteps: [], context: {}, timestamp: Date.now(), version: 1 });
    cm.save({ id: 'cp-2', workflowId: 'w2', completedSteps: [], context: {}, timestamp: Date.now(), version: 1 });
    expect(cm.list()).toEqual(['w1', 'w2']);
  });
});
