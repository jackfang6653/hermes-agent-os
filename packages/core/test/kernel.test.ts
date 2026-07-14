// SPDX-License-Identifier: MIT
import { describe, it, expect, vi } from 'vitest';
import { Kernel } from '../src/kernel.js';
import { EventBus } from '../src/event-bus.js';
import { Scheduler } from '../src/scheduler.js';
import { ConfigLoader } from '../src/config/loader.js';
import type { PluginManifest, LifecycleMethods } from '../src/types.js';

describe('Kernel', () => {
  it('should start and stop', async () => {
    const kernel = new Kernel({ name: 'test', version: '1.0' });
    expect(kernel.state).toBe('init');
    await kernel.start();
    expect(kernel.state).toBe('running');
    await kernel.stop();
    expect(kernel.state).toBe('stopped');
  });

  it('should load and manage plugins', async () => {
    const kernel = new Kernel({ name: 'test', version: '1.0' });
    const manifest: PluginManifest = {
      id: 'p1', name: 'TestPlugin', version: '1.0',
      description: 'Test', dependencies: [], hooks: ['onInit', 'onStart'],
    };
    const instance: LifecycleMethods = {
      onInit: vi.fn().mockResolvedValue(undefined),
      onStart: vi.fn().mockResolvedValue(undefined),
    };
    const loaded = kernel.loadPlugin(manifest, instance);
    expect(loaded).toBe(true);
    expect(kernel.hasPlugin('p1')).toBe(true);
    expect(kernel.pluginCount).toBe(1);

    await kernel.start();
    expect(instance.onStart).toHaveBeenCalled();
  });

  it('should emit events through bus', async () => {
    const kernel = new Kernel({ name: 'event-test', version: '1.0' });
    const events: string[] = [];
    kernel.eventBus.on('kernel:starting', (e) => { events.push(e.type); });
    await kernel.start();
    expect(events).toContain('kernel:starting');
  });

  it('should handle errors', () => {
    const kernel = new Kernel({ name: 'err-test', version: '1.0' });
    const errors: string[] = [];
    kernel.eventBus.on('kernel:error', (e) => { errors.push((e.data as any)?.message); });
    kernel.handleError(new Error('test error'));
    expect(errors).toContain('test error');
  });
});

describe('EventBus', () => {
  it('should emit and listen', () => {
    const bus = new EventBus();
    const events: string[] = [];
    bus.on('test', (e) => { events.push(e.type); });
    bus.emit({ type: 'test', source: 's', timestamp: 1 });
    expect(events).toHaveLength(1);
  });

  it('should support wildcard listener', () => {
    const bus = new EventBus();
    const all: string[] = [];
    bus.on('*', (e) => { all.push(e.type); });
    bus.emit({ type: 'a', source: 's', timestamp: 1 });
    bus.emit({ type: 'b', source: 's', timestamp: 2 });
    expect(all).toEqual(['a', 'b']);
  });

  it('should maintain history', () => {
    const bus = new EventBus(3);
    for (let i = 0; i < 5; i++) {
      bus.emit({ type: `e${i}`, source: 's', timestamp: i });
    }
    expect(bus.getHistory()).toHaveLength(3);
    expect(bus.getHistory('e4')).toHaveLength(1);
  });
});

describe('Scheduler', () => {
  it('should schedule and cancel', async () => {
    const s = new Scheduler();
    s.start();
    const fn = vi.fn();
    s.scheduleOnce('task1', fn, 10);
    expect(s.has('task1')).toBe(true);
    await new Promise(r => setTimeout(r, 50));
    expect(fn).toHaveBeenCalled();
    expect(s.has('task1')).toBe(false);
    s.stop();
  });

  it('should list tasks', () => {
    const s = new Scheduler();
    s.schedule('t1', async () => {}, 1000);
    const list = s.list();
    expect(list).toHaveLength(1);
    expect(list[0].id).toBe('t1');
    s.stop();
  });
});

describe('ConfigLoader', () => {
  it('should load from env with prefix', () => {
    process.env['HERMES_DEBUG'] = 'true';
    process.env['HERMES_PORT'] = '8080';
    const loader = new ConfigLoader();
    loader.loadFromEnv('HERMES_');
    expect(loader.get('debug')).toBe(true);
    expect(loader.get('port')).toBe(8080);
  });

  it('should merge configs', () => {
    const loader = new ConfigLoader();
    loader.merge({ key1: 'val1', key2: 42 });
    expect(loader.get('key1')).toBe('val1');
    expect(loader.get('key2')).toBe(42);
  });

  it('should validate required keys', () => {
    const loader = new ConfigLoader();
    loader.merge({ a: 1 });
    const missing = loader.validate(['a', 'b', 'c']);
    expect(missing).toEqual(['b', 'c']);
  });
});
