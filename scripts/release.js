#!/usr/bin/env node
// SPDX-License-Identifier: MIT
// Hermes Agent OS — 版本管理 + 发布脚本
// 用法: node scripts/release.js <major|minor|patch>

import { readFileSync, writeFileSync } from 'node:fs';
import { execSync } from 'node:child_process';

const bumpType = process.argv[2] || 'patch';
if (!['major', 'minor', 'patch'].includes(bumpType)) {
  console.error('Usage: node scripts/release.js <major|minor|patch>');
  process.exit(1);
}

const ROOT = new URL('..', import.meta.url).pathname;
const pkgPath = `${ROOT}/package.json`;

// Read root package.json
const pkg = JSON.parse(readFileSync(pkgPath, 'utf-8'));
const [major, minor, patch] = pkg.version.split('.').map(Number);

let newVersion;
switch (bumpType) {
  case 'major': newVersion = `${major + 1}.0.0`; break;
  case 'minor': newVersion = `${major}.${minor + 1}.0`; break;
  case 'patch': newVersion = `${major}.${minor}.${patch + 1}`; break;
}

console.log(`\n  📦 Hermes Agent OS Release`);
console.log(`  ────────────────────────`);
console.log(`  Current: v${pkg.version}`);
console.log(`  Target:  v${newVersion}\n`);

// Update root version
pkg.version = newVersion;
writeFileSync(pkgPath, JSON.stringify(pkg, null, 2) + '\n');
console.log(`  ✅ Root package.json → v${newVersion}`);

// Update all workspace packages
import { globSync } from 'node:fs';
const packages = globSync('packages/*/package.json', { cwd: ROOT });
for (const p of packages) {
  const pp = JSON.parse(readFileSync(`${ROOT}/${p}`, 'utf-8'));
  if (p.includes('node_modules')) continue;
  pp.version = newVersion;
  writeFileSync(`${ROOT}/${p}`, JSON.stringify(pp, null, 2) + '\n');
  console.log(`  ✅ ${p} → v${newVersion}`);
}

// Generate CHANGELOG entry
const date = new Date().toISOString().split('T')[0];
const changelog = `\n## [${newVersion}] - ${date}\n\n### Added\n- Release v${newVersion}\n\n### Changed\n- ${getChanges()}\n`;

// Prepend to CHANGELOG
try {
  const existing = readFileSync(`${ROOT}/CHANGELOG.md`, 'utf-8');
  writeFileSync(`${ROOT}/CHANGELOG.md`, changelog + existing);
} catch {
  writeFileSync(`${ROOT}/CHANGELOG.md`, `# Changelog\n${changelog}`);
}
console.log(`  ✅ CHANGELOG.md updated`);

// Git tag
execSync(`git add -A && git commit -m "chore: release v${newVersion}"`, { cwd: ROOT, stdio: 'inherit' });
execSync(`git tag v${newVersion}`, { cwd: ROOT, stdio: 'inherit' });
execSync(`git push origin master --tags`, { cwd: ROOT, stdio: 'inherit' });

console.log(`\n  ✅ v${newVersion} released!\n`);

function getChanges(): string {
  try {
    const log = execSync('git log --oneline --no-decorate -10', { cwd: ROOT, encoding: 'utf-8' });
    return log.split('\n').filter(Boolean).slice(0, 5).join('; ');
  } catch {
    return 'Various improvements';
  }
}
