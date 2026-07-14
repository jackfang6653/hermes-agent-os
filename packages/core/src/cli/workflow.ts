// SPDX-License-Identifier: MIT

export async function workflowCommand(
  workflowId: string,
  options: { context?: string },
) {
  console.log(`\n  ⚡ Running workflow: ${workflowId}`);
  const context = options.context ? JSON.parse(options.context) : {};

  try {
    const mod = await import('@hermes-os/workflow-engine');
    const engine = new mod.WorkflowEngine();
    engine.registerHandler('analyze', async (_step: any, _ctx: any) => ({ status: 'ok', data: _ctx }));
    engine.registerHandler('export', async (_step: any, _ctx: any) => ({ status: 'ok', data: _ctx }));

    const result = await engine.start(workflowId, context);
    console.log(`  ✅ Workflow ${result.status}`);
    if (result.error) console.error(`  ❌ ${result.error}`);
  } catch (e: any) {
    console.error(`  ❌ ${e.message}`);
  }
}
