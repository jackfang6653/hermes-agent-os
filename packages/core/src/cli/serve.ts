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
    // Dynamic import — at runtime pnpm links workspace packages
    const mod = await import('@hermes-os/backend');
    const server = mod as { createServer?: (port: number, host: string) => Promise<{ close: () => void }> };
    if (server.createServer) {
      await server.createServer(port, options.host);
    } else {
      console.log('  Server module loaded but createServer not found');
    }
  } catch (e: any) {
    console.error(`  ❌ ${e.message}`);
    console.log('\n  To start the server directly:\n    node packages/backend/dist/server.js\n');
  }
}
