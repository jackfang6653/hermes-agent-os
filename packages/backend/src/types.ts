// SPDX-License-Identifier: MIT

export interface RouteDef {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  path: string;
  handler: string;
  auth: boolean;
  description: string;
}

export type RouteHandler<TReq, TRes> = (
  request: ApiRequest<TReq>,
) => Promise<ApiResponse<TRes>>;

export interface ApiRequest<T = unknown> {
  body: T;
  params: Record<string, string>;
  query: Record<string, string>;
  headers: Record<string, string>;
  userId?: string;
  timestamp: number;
}

export interface ApiResponse<T = unknown> {
  status: number;
  data?: T;
  error?: string;
  meta?: {
    page?: number;
    pageSize?: number;
    total?: number;
    duration: number;
  };
}

export interface ServerConfig {
  port: number;
  host: string;
  corsOrigins: string[];
  rateLimit: { maxRequests: number; windowMs: number };
  auth: { jwtSecret: string; tokenExpiry: string };
}

export interface WebSocketEvent {
  type: string;
  channel: string;
  payload: unknown;
  userId?: string;
}

export interface MCPToolDef {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
  handler: string;
}
