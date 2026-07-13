// SPDX-License-Identifier: MIT

import * as fs from 'fs';
import * as path from 'path';

export class ConfigLoader {
  private config: Record<string, unknown> = {};

  loadFromFile(filePath: string): Record<string, unknown> {
    const ext = path.extname(filePath).toLowerCase();
    let content: string;
    try {
      content = fs.readFileSync(filePath, 'utf-8');
    } catch {
      throw new Error(`Config file not found: ${filePath}`);
    }

    if (ext === '.json') {
      this.config = { ...this.config, ...JSON.parse(content) };
    } else if (ext === '.yaml' || ext === '.yml') {
      throw new Error('YAML loader not available — use JSON or .env');
    } else {
      throw new Error(`Unsupported config format: ${ext}`);
    }

    return this.config;
  }

  loadFromEnv(prefix = 'HERMES_'): Record<string, unknown> {
    const envConfig: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(process.env)) {
      if (key.startsWith(prefix)) {
        const configKey = key.slice(prefix.length).toLowerCase().replace(/_/g, '.');
        envConfig[configKey] = this._coerce(value ?? '');
      }
    }
    this.config = { ...this.config, ...envConfig };
    return this.config;
  }

  get<T>(key: string, defaultValue?: T): T | undefined {
    return (this.config[key] as T) ?? defaultValue;
  }

  getAll(): Record<string, unknown> {
    return { ...this.config };
  }

  merge(partial: Record<string, unknown>): void {
    this.config = { ...this.config, ...partial };
  }

  validate(required: string[]): string[] {
    return required.filter(key => !(key in this.config));
  }

  private _coerce(value: string): string | number | boolean {
    if (value === 'true') return true;
    if (value === 'false') return false;
    const num = Number(value);
    if (!isNaN(num) && value.trim() !== '') return num;
    return value;
  }
}
