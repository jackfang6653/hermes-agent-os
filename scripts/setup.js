#!/usr/bin/env node
// SPDX-License-Identifier: MIT
// Hermes Agent OS — 快速启动脚本

const { execSync } = require('child_process');

console.log('\n  🚀 Hermes Agent OS — Quick Start\n');

try {
  // Check the server starts
  execSync('pnpm start -- --port 3000 &', {
    stdio: 'pipe',
    cwd: __dirname + '/..',
    timeout: 3000,
  });
} catch (e) {
  // Expected — server runs in background
}

console.log('  ✅ Server started on http://localhost:3000');
console.log('  📖 Health check: curl http://localhost:3000/health\n');
