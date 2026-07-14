// SPDX-License-Identifier: MIT

export async function configCommand(options: {
  get?: string;
  set?: [string, string];
  list?: boolean;
}) {
  try {
    const { ConfigLoader } = await import('../config/loader.js');
    const loader = new ConfigLoader();

    if (options.list) {
      loader.loadFromEnv('HERMES_');
      console.log('\n  📋 Current Configuration:');
      console.log('  ─────────────────────────');
      for (const [key, value] of Object.entries(loader.getAll())) {
        console.log(`  ${key}: ${value}`);
      }
    } else if (options.get) {
      loader.loadFromEnv('HERMES_');
      const value = loader.get(options.get);
      console.log(`\n  ${options.get} = ${value ?? '(not set)'}`);
    } else {
      console.log('\n  Usage: hermes config --list');
      console.log('         hermes config --get <key>');
      console.log('         hermes config --set <key> <value>\n');
    }
  } catch (e: any) {
    console.error(`  ❌ ${e.message}`);
  }
}
