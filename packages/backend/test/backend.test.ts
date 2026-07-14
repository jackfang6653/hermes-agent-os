// SPDX-License-Identifier: MIT
import { describe, it, expect } from 'vitest';
import { ROUTES, findRouteDef } from '../src/routes';
import { DEFAULT_CONFIG, createAppConfig } from '../src/config';
import { handlers } from '../src/handlers';
import { MCP_TOOLS } from '../src/mcp';

describe('API Routes', () => {
  it('should have defined routes', () => {
    expect(ROUTES.length).toBeGreaterThan(10);
  });

  it('should find route by method and path', () => {
    const route = findRouteDef('GET', '/api/projects');
    expect(route?.handler).toBe('listProjects');
  });

  it('should match parameterized routes', () => {
    const route = findRouteDef('GET', '/api/projects/abc123');
    expect(route?.handler).toBe('getProject');
  });

  it('should return undefined for unknown routes', () => {
    expect(findRouteDef('GET', '/unknown')).toBeUndefined();
  });
});

describe('Server Config', () => {
  it('should have default values', () => {
    expect(DEFAULT_CONFIG.port).toBe(3000);
    expect(DEFAULT_CONFIG.auth.jwtSecret).toBeTruthy();
  });

  it('should merge overrides', () => {
    const config = createAppConfig({ port: 8080 });
    expect(config.port).toBe(8080);
    expect(config.host).toBe('0.0.0.0'); // unchanged
  });
});

describe('Handlers', () => {
  it('health check should return ok', async () => {
    const res = await handlers.healthCheck({} as any);
    expect(res.status).toBe(200);
  });

  it('listProjects should return array', async () => {
    const res = await handlers.listProjects({} as any);
    expect(Array.isArray(res.data)).toBe(true);
  });
});

describe('MCP Tools', () => {
  it('should have 5 tools defined', () => {
    expect(MCP_TOOLS).toHaveLength(5);
  });

  it('each tool should have required fields', () => {
    for (const tool of MCP_TOOLS) {
      expect(tool.name).toBeTruthy();
      expect(tool.description).toBeTruthy();
      expect(tool.handler).toBeTruthy();
    }
  });
});
