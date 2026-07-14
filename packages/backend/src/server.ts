// SPDX-License-Identifier: MIT

import type { ApiRequest, ApiResponse } from './types.js';
import { ROUTES } from './routes.js';
import { handlers } from './handlers.js';

export interface ServerInstance {
  close: () => void;
}

export async function createServer(
  port = 3000,
  host = '0.0.0.0',
): Promise<ServerInstance> {
  // Native HTTP server — zero dependencies
  const http = await import('node:http');
  const url = await import('node:url');

  const server = http.createServer(async (req, res) => {
    // CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type,Authorization');
    if (req.method === 'OPTIONS') {
      res.writeHead(204);
      res.end();
      return;
    }

    const parsedUrl = new URL(req.url ?? '/', `http://${host}:${port}`);
    const pathname = parsedUrl.pathname;
    const method = req.method ?? 'GET';

    // Find matching route
    const route = ROUTES.find(r => {
      if (r.method !== method) return false;
      const pattern = r.path.replace(/:id/g, '[^/]+').replace(/:([^/]+)/g, '[^/]+');
      return new RegExp(`^${pattern}$`).test(pathname);
    });

    if (!route) {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Not found' }));
      return;
    }

    // Extract params
    const params: Record<string, string> = {};
    const routeParts = route.path.split('/');
    const pathParts = pathname.split('/');
    routeParts.forEach((part, i) => {
      if (part.startsWith(':')) {
        params[part.slice(1)] = pathParts[i] ?? '';
      }
    });

    // Read body
    let body = '';
    if (method === 'POST' || method === 'PUT') {
      await new Promise<void>((resolve) => {
        req.on('data', (chunk: Buffer) => { body += chunk.toString(); });
        req.on('end', () => resolve());
      });
    }

    const request: ApiRequest = {
      body: body ? JSON.parse(body) : {},
      params,
      query: Object.fromEntries(parsedUrl.searchParams),
      headers: req.headers as Record<string, string>,
      timestamp: Date.now(),
    };

    try {
      const handler = handlers[route.handler as keyof typeof handlers];
      if (!handler) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: `Handler '${route.handler}' not found` }));
        return;
      }
      const result = await handler(request);
      res.writeHead(result.status, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(result));
    } catch (err: any) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: err.message }));
    }
  });

  return new Promise((resolve) => {
    server.listen(port, host, () => {
      resolve({ close: () => server.close() });
    });
  });
}
