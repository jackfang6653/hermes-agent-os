// SPDX-License-Identifier: MIT
import { describe, it, expect } from 'vitest';
import { MemoryStore } from '../src/store.js';
import { SnapshotManager, RetentionManager } from '../src/snapshots.js';

describe('MemoryStore', () => {
  it('should set and get values', () => {
    const store = new MemoryStore();
    store.set('name', 'NORHOR', { type: 'persistent', tags: ['brand'] });
    const entry = store.get('name');
    expect(entry?.value).toBe('NORHOR');
    expect(entry?.type).toBe('persistent');
  });

  it('should get typed values', () => {
    const store = new MemoryStore();
    store.set('count', 42);
    expect(store.getValue<number>('count')).toBe(42);
  });

  it('should query by type', () => {
    const store = new MemoryStore();
    store.set('a', 1, { type: 'session' });
    store.set('b', 2, { type: 'persistent' });
    store.set('c', 3, { type: 'session' });
    expect(store.query({ type: 'session' })).toHaveLength(2);
  });

  it('should query by tags', () => {
    const store = new MemoryStore();
    store.set('key1', 'v1', { tags: ['tag1'] });
    store.set('key2', 'v2', { tags: ['tag1', 'tag2'] });
    store.set('key3', 'v3', { tags: ['tag2'] });
    expect(store.query({ tags: ['tag1'] })).toHaveLength(2);
  });

  it('should delete entries', () => {
    const store = new MemoryStore();
    store.set('temp', 'value');
    expect(store.delete('temp')).toBe(true);
    expect(store.get('temp')).toBeUndefined();
  });

  it('should handle expiry', async () => {
    const store = new MemoryStore();
    store.set('ephemeral', 'short-lived', { ttl: 10 });
    expect(store.get('ephemeral')).toBeDefined();
    await new Promise(r => setTimeout(r, 30));
    expect(store.get('ephemeral')).toBeUndefined();
  }, 10000);

  it('should cleanup expired entries', () => {
    const store = new MemoryStore();
    store.set('expired', 'old', { ttl: -1000 });
    store.set('valid', 'good', { type: 'persistent' });
    const cleaned = store.cleanup();
    expect(cleaned).toBeGreaterThanOrEqual(1);
  });

  it('should enforce max entries', () => {
    const store = new MemoryStore(3);
    store.set('a', 1);
    store.set('b', 2);
    store.set('c', 3);
    store.set('d', 4); // should evict 'a'
    expect(store.count()).toBe(3);
  });
});

describe('SnapshotManager', () => {
  it('should save and restore checkpoints', () => {
    const sm = new SnapshotManager();
    sm.save('check-1', { progress: 50 });
    const restored = sm.restore('check-1');
    expect(restored?.data.progress).toBe(50);
  });

  it('should increment version on re-save', () => {
    const sm = new SnapshotManager();
    sm.save('cp', {});
    sm.save('cp', {});
    const cp = sm.restore('cp');
    expect(cp?.version).toBe(2);
  });

  it('should list checkpoints sorted by time', async () => {
    const sm = new SnapshotManager();
    sm.save('first', {});
    await new Promise(r => setTimeout(r, 10));
    sm.save('second', {});
    const list = sm.list();
    expect(list[0].label).toBe('second');
  });
});

describe('RetentionManager', () => {
  it('should enforce retention policies', () => {
    const store = new MemoryStore();
    const rm = new RetentionManager(store, { maxAge: 1000, maxEntriesPerType: 2 });
    store.set('a', 1, { type: 'cache' });
    store.set('b', 2, { type: 'cache' });
    store.set('c', 3, { type: 'cache' });
    const cleaned = rm.enforce();
    expect(cleaned).toBeGreaterThanOrEqual(1);
    expect(store.query({ type: 'cache' }).length).toBeLessThanOrEqual(2);
  });
});
