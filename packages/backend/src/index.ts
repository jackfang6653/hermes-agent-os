// SPDX-License-Identifier: MIT

export { ROUTES, findRouteDef } from './routes.js';
export { DEFAULT_CONFIG, createAppConfig } from './config.js';
export { handlers } from './handlers.js';
export { MCP_TOOLS } from './mcp.js';
export type {
  RouteDef,
  RouteHandler,
  ApiRequest,
  ApiResponse,
  ServerConfig,
  WebSocketEvent,
  MCPToolDef,
} from './types.js';
export const VERSION = '1.0.0';
