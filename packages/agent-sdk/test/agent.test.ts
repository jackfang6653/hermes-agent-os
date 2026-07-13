// SPDX-License-Identifier: MIT
import { describe, it, expect, vi } from 'vitest';
import { Agent } from '../src/agent';
import { AgentRegistry } from '../src/registry';
import { MessageBus } from '../src/message-bus';
import { RuntimeContext } from '../src/runtime';
import type { AgentConfig, Message } from '../src/types';

class TestAgent extends Agent {
  protected async onInit() { /* noop */ }
  protected async onStop() { /* noop */ }
}

describe('Agent', () => {
  const config: AgentConfig = { id: 'test-1', name: 'TestAgent', capabilities: ['test'] };

  it('should create and start', async () => {
    const agent = new TestAgent(config);
    expect(agent.getStatus()).toBe('idle');
    await agent.start();
    expect(agent.getStatus()).toBe('running');
    expect(agent.getUptime()).toBeGreaterThanOrEqual(0);
  });

  it('should stop correctly', async () => {
    const agent = new TestAgent(config);
    await agent.start();
    await agent.stop();
    expect(agent.getStatus()).toBe('stopped');
  });

  it('should handle messages via registered handler', async () => {
    const agent = new TestAgent(config);
    const handler = vi.fn().mockResolvedValue(undefined);
    agent.registerHandler('request', handler);
    const msg: Message = { id: 'm1', from: 'sender', to: 'test-1', type: 'request', payload: {}, timestamp: Date.now() };
    await agent.handleMessage(msg);
    expect(handler).toHaveBeenCalledWith(msg);
  });

  it('should set capabilities', () => {
    const agent = new TestAgent(config);
    agent.setCapability({ name: 'vision', version: '1.0', description: 'Visual analysis' });
    expect(agent.capabilities).toHaveLength(1);
    expect(agent.capabilities[0].name).toBe('vision');
  });
});

describe('AgentRegistry', () => {
  it('should register and retrieve agents', () => {
    const registry = new AgentRegistry();
    const agent = new TestAgent({ id: 'a1', name: 'A1', capabilities: ['vision'] });
    registry.register(agent);
    expect(registry.count()).toBe(1);
    expect(registry.getAgent('a1')).toBe(agent);
  });

  it('should find agents by capability', () => {
    const registry = new AgentRegistry();
    const a1 = new TestAgent({ id: 'a1', name: 'A1', capabilities: [] });
    a1.setCapability({ name: 'vision', version: '1.0', description: '' });
    registry.register(a1);
    registry.register(new TestAgent({ id: 'a2', name: 'A2', capabilities: [] }));
    const found = registry.findAgentsByCapability('vision');
    expect(found).toHaveLength(1);
    expect(found[0].id).toBe('a1');
  });

  it('should unregister agents', () => {
    const registry = new AgentRegistry();
    registry.register(new TestAgent({ id: 'a1', name: 'A1', capabilities: [] }));
    registry.unregister('a1');
    expect(registry.count()).toBe(0);
  });
});

describe('MessageBus', () => {
  it('should publish and subscribe', async () => {
    const bus = new MessageBus();
    const messages: Message[] = [];
    bus.subscribe('request', async (msg) => { messages.push(msg); });
    await bus.publish({ id: 'm1', from: 'a', to: 'b', type: 'request', payload: {}, timestamp: Date.now() });
    expect(messages).toHaveLength(1);
  });

  it('should support wildcard subscription', async () => {
    const bus = new MessageBus();
    const messages: Message[] = [];
    bus.subscribe('*', async (msg) => { messages.push(msg); });
    await bus.publish({ id: 'm1', from: 'a', to: 'b', type: 'event', payload: {}, timestamp: Date.now() });
    expect(messages).toHaveLength(1);
  });

  it('should maintain history', async () => {
    const bus = new MessageBus(10);
    for (let i = 0; i < 5; i++) {
      await bus.publish({ id: `m${i}`, from: 'a', to: 'b', type: 'event', payload: {}, timestamp: Date.now() });
    }
    expect(bus.getHistory()).toHaveLength(5);
  });
});

describe('RuntimeContext', () => {
  it('should set and get values', () => {
    const ctx = new RuntimeContext('agent-1', { debug: true });
    ctx.set('key', 'value');
    expect(ctx.get('key')).toBe('value');
    expect(ctx.config.debug).toBe(true);
  });

  it('should register and execute tools', async () => {
    const ctx = new RuntimeContext('agent-1');
    ctx.registerTool('echo', async (x) => x);
    const result = await ctx.executeTool('echo', 'hello');
    expect(result).toBe('hello');
  });
});
