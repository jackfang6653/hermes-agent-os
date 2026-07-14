#!/usr/bin/env node
// SPDX-License-Identifier: MIT
// Hermes Agent OS — 项目初始化脚本
// 用法: node scripts/bootstrap.js

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function run(cmd) {
  console.log(`\n> ${cmd}`);
  execSync(cmd, { stdio: 'inherit', cwd: __dirname + '/..' });
}

function main() {
  console.log('\n  🚀 Hermes Agent OS Bootstrap');
  console.log('  ──────────────────────────\n');

  // 1. 复制 .env
  const envPath = path.join(__dirname, '..', '.env');
  if (!fs.existsSync(envPath)) {
    fs.copyFileSync(path.join(__dirname, '..', '.env.example'), envPath);
    console.log('  ✅ .env created (edit with your API keys)');
  } else {
    console.log('  ⏭️  .env already exists');
  }

  // 2. Install deps
  run('pnpm install');

  // 3. Type check
  run('pnpm -r exec tsc --noEmit');

  // 4. Build
  run('pnpm -r exec tsc --outDir dist');

  console.log('\n  ✅ Hermes Agent OS is ready!');
  console.log('  ─────────────────────────────');
  console.log('  pnpm serve    — Start API server');
  console.log('  pnpm cli      — CLI help');
  console.log('  pnpm test     — Run tests\n');
}

main();
