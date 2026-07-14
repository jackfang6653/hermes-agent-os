// SPDX-License-Identifier: MIT

export async function serveCommand(options: { port: string; host: string }) {
  const port = parseInt(options.port, 10);
  console.log(`\n  🚀 Hermes Agent OS Server`);
  console.log(`  ─────────────────────`);
  console.log(`  Server starting on http://${options.host}:${port}`);
  console.log(`  Health: http://${options.host}:${port}/health`);
  console.log(`  API:    http://${options.host}:${port}/api`);
  console.log(`\n  Press Ctrl+C to stop\n`);

  try {
    // dynamic import — works at runtime via workspace link
    const mod = await import('@hermes-os/backend');
    const server = mod as any;
    if (server.createServer) {
      await server.createServer(port, options.host);
    } else {
      console.log(`  Server module loaded. Install express to start:`);
      console.log(`  pnpm add express @types/express --filter @hermes-os/backend`);
    }
  } catch (e: any) {
    console.error(`  ❌ ${e.message}`);
  }
}
