// SPDX-License-Identifier: MIT

export class RuntimeContext {
  private store = new Map<string, unknown>();
  private toolRegistry = new Map<string, (...args: unknown[]) => Promise<unknown>>();

  constructor(
    public readonly agentId: string,
    public readonly config: Record<string, unknown> = {},
  ) {}

  get<T>(key: string): T | undefined {
    return this.store.get(key) as T | undefined;
  }

  set<T>(key: string, value: T): void {
    this.store.set(key, value);
  }

  has(key: string): boolean {
    return this.store.has(key);
  }

  delete(key: string): boolean {
    return this.store.delete(key);
  }

  get memory(): Map<string, unknown> {
    return this.store;
  }

  get tools(): Map<string, (...args: unknown[]) => Promise<unknown>> {
    return this.toolRegistry;
  }

  registerTool(name: string, fn: (...args: unknown[]) => Promise<unknown>): void {
    this.toolRegistry.set(name, fn);
  }

  async executeTool(name: string, ...args: unknown[]): Promise<unknown> {
    const tool = this.toolRegistry.get(name);
    if (!tool) throw new Error(`Tool '${name}' not found`);
    return tool(...args);
  }

  toJSON(): Record<string, unknown> {
    return {
      agentId: this.agentId,
      config: this.config,
      memories: Array.from(this.store.keys()),
      tools: Array.from(this.toolRegistry.keys()),
    };
  }
}
