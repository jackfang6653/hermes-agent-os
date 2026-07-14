// SPDX-License-Identifier: MIT

export { ROUTES, findRouteDef } from './routes';
export { DEFAULT_CONFIG, createAppConfig } from './config';
export { handlers } from './handlers';
export { MCP_TOOLS } from './mcp';
export type {
  RouteDef,
  RouteHandler,
  ApiRequest,
  ApiResponse,
  ServerConfig,
  WebSocketEvent,
  MCPToolDef,
} from './types';
export const VERSION = '1.0.0';
