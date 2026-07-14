// SPDX-License-Identifier: MIT

export async function workflowCommand(
  workflowId: string,
  options: { context?: string },
) {
  console.log(`\n  ⚡ Running workflow: ${workflowId}`);
  const context = options.context ? JSON.parse(options.context) : {};

  try {
    const { WorkflowEngine } = await import('@hermes-os/workflow-engine');
    const engine = new WorkflowEngine();
    engine.registerHandler('analyze', async (_step, ctx) => ({ status: 'ok', data: ctx }));
    engine.registerHandler('export', async (_step, ctx) => ({ status: 'ok', data: ctx }));

    const result = await engine.start(workflowId, context);
    console.log(`  ✅ Workflow ${result.status}`);
    if (result.error) console.error(`  ❌ ${result.error}`);
  } catch (e: any) {
    console.error(`  ❌ ${e.message}`);
  }
}
