// SPDX-License-Identifier: MIT

import type { ServerConfig } from './types.js';

export const DEFAULT_CONFIG: ServerConfig = {
  port: 3000,
  host: '0.0.0.0',
  corsOrigins: ['*'],
  rateLimit: { maxRequests: 100, windowMs: 60000 },
  auth: { jwtSecret: 'change-me-in-production', tokenExpiry: '24h' },
};

export function createAppConfig(overrides?: Partial<ServerConfig>): ServerConfig {
  return { ...DEFAULT_CONFIG, ...overrides };
}
