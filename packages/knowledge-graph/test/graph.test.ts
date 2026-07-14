// SPDX-License-Identifier: MIT
import { describe, it, expect } from 'vitest';
import { Graph } from '../src/graph.js';
import { QueryEngine } from '../src/query.js';
import type { BrandNode, ProductNode, SceneNode } from '../src/types.js';

function createTestGraph(): Graph {
  const g = new Graph('test', '1.0.0');

  const brand: BrandNode = {
    id: 'brand-1',
    type: 'brand',
    label: 'NORHOR',
    properties: { name: 'NORHOR', style: ['nordic', 'minimal'], positioning: ['modern'] },
    metadata: { createdAt: '2024-01-01', updatedAt: '2024-01-01' },
  };

  const sofa: ProductNode = {
    id: 'prod-1',
    type: 'product',
    label: 'Cloud Sofa',
    properties: { sku: 'CS-001', brandId: 'brand-1', categoryId: 'cat-1', dimensions: '200x80x70', materials: ['linen', 'wood'], color: 'beige', status: 'active' },
    metadata: { createdAt: '2024-01-01', updatedAt: '2024-01-01' },
  };

  const chair: ProductNode = {
    id: 'prod-2',
    type: 'product',
    label: 'Wishbone Chair',
    properties: { sku: 'WC-001', brandId: 'brand-1', categoryId: 'cat-2', dimensions: '55x80x90', materials: ['wood'], color: 'natural', status: 'active' },
    metadata: { createdAt: '2024-01-01', updatedAt: '2024-01-01' },
  };

  const scene: SceneNode = {
    id: 'scene-1',
    type: 'scene',
    label: 'Nordic Living Room',
    properties: { style: 'nordic', moodKeywords: ['calm', 'warm'], colorPalette: ['#f5f0e8', '#d4c5b0'] },
    metadata: { createdAt: '2024-01-01', updatedAt: '2024-01-01' },
  };

  g.addNode(brand);
  g.addNode(sofa);
  g.addNode(chair);
  g.addNode(scene);

  g.addEdge({ id: 'e1', source: 'prod-1', target: 'brand-1', relationship: 'BELONGS_TO', weight: 1, properties: {} });
  g.addEdge({ id: 'e2', source: 'prod-2', target: 'brand-1', relationship: 'BELONGS_TO', weight: 1, properties: {} });
  g.addEdge({ id: 'e3', source: 'prod-1', target: 'scene-1', relationship: 'RECOMMENDS', weight: 1, properties: {} });

  return g;
}

describe('Knowledge Graph', () => {
  it('should add and retrieve nodes', () => {
    const g = createTestGraph();
    const node = g.getNode('brand-1');
    expect(node).toBeDefined();
    expect(node?.label).toBe('NORHOR');
  });

  it('should find nodes by type', () => {
    const g = createTestGraph();
    const products = g.findNodesByType('product');
    expect(products).toHaveLength(2);
  });

  it('should get neighbors', () => {
    const g = createTestGraph();
    const neighbors = g.getNeighbors('prod-1');
    expect(neighbors).toHaveLength(2); // brand-1 + scene-1
  });

  it('should perform BFS traversal', () => {
    const g = createTestGraph();
    const result = g.bfs('brand-1');
    expect(result.length).toBeGreaterThanOrEqual(3);
  });

  it('should find shortest path', () => {
    const g = createTestGraph();
    const path = g.shortestPath('prod-2', 'scene-1');
    expect(path).toEqual(['prod-2', 'brand-1', 'prod-1', 'scene-1']);
  });

  it('should serialize and deserialize', () => {
    const g = createTestGraph();
    const json = g.toJSON();
    const restored = Graph.fromJSON(json);
    expect(restored.getNode('brand-1')?.label).toBe('NORHOR');
    expect(restored.getEdges()).toHaveLength(3);
  });
});

describe('QueryEngine', () => {
  it('should query products by brand', () => {
    const g = createTestGraph();
    const qe = new QueryEngine(g);
    const results = qe.queryProducts({ brandId: 'brand-1' });
    expect(results).toHaveLength(2);
  });

  it('should recommend scenes by product', () => {
    const g = createTestGraph();
    const qe = new QueryEngine(g);
    const scenes = qe.recommendScenes({ productId: 'prod-1' });
    expect(scenes.length).toBeGreaterThanOrEqual(1);
    expect(scenes[0]?.label).toBe('Nordic Living Room');
  });
});
