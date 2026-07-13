// SPDX-License-Identifier: MIT

import type { GraphNode, GraphEdge, KnowledgeGraph, NodeType, RelationshipType } from './types';

export class Graph {
  private nodes: Map<string, GraphNode> = new Map();
  private edges: GraphEdge[] = [];
  private adjacencyList: Map<string, string[]> = new Map();

  constructor(name = 'default', version = '1.0.0') {
    this.nodes = new Map();
    this.edges = [];
    this.adjacencyList = new Map();
    this.metadata = { name, version, nodeCount: 0, edgeCount: 0 };
  }

  metadata: { name: string; version: string; nodeCount: number; edgeCount: number };

  // ─── Node Operations ──────────────────────────────

  addNode<T>(node: GraphNode<T>): void {
    this.nodes.set(node.id, node as GraphNode);
    this.adjacencyList.set(node.id, []);
    this.metadata.nodeCount = this.nodes.size;
  }

  getNode(id: string): GraphNode | undefined {
    return this.nodes.get(id);
  }

  findNodesByType(type: NodeType): GraphNode[] {
    const result: GraphNode[] = [];
    for (const node of this.nodes.values()) {
      if (node.type === type) result.push(node);
    }
    return result;
  }

  findNodes(query: (node: GraphNode) => boolean): GraphNode[] {
    const result: GraphNode[] = [];
    for (const node of this.nodes.values()) {
      if (query(node)) result.push(node);
    }
    return result;
  }

  removeNode(id: string): boolean {
    const existed = this.nodes.delete(id);
    this.adjacencyList.delete(id);
    // remove edges connected to this node
    this.edges = this.edges.filter(e => e.source !== id && e.target !== id);
    // clean adjacency
    for (const [, neighbors] of this.adjacencyList) {
      const idx = neighbors.indexOf(id);
      if (idx !== -1) neighbors.splice(idx, 1);
    }
    if (existed) {
      this.metadata.nodeCount = this.nodes.size;
      this.metadata.edgeCount = this.edges.length;
    }
    return existed;
  }

  // ─── Edge Operations ──────────────────────────────

  addEdge(edge: GraphEdge): boolean {
    if (!this.nodes.has(edge.source) || !this.nodes.has(edge.target)) {
      return false;
    }
    this.edges.push(edge);
    this.adjacencyList.get(edge.source)?.push(edge.target);
    this.adjacencyList.get(edge.target)?.push(edge.source);
    this.metadata.edgeCount = this.edges.length;
    return true;
  }

  getEdges(nodeId?: string): GraphEdge[] {
    if (!nodeId) return this.edges;
    return this.edges.filter(e => e.source === nodeId || e.target === nodeId);
  }

  findEdges(relationship?: RelationshipType): GraphEdge[] {
    if (!relationship) return this.edges;
    return this.edges.filter(e => e.relationship === relationship);
  }

  // ─── Traversal ───────────────────────────────────

  getNeighbors(nodeId: string): GraphNode[] {
    const neighborIds = this.adjacencyList.get(nodeId) || [];
    return neighborIds.map(id => this.nodes.get(id)).filter(Boolean) as GraphNode[];
  }

  bfs(startId: string): GraphNode[] {
    const visited = new Set<string>();
    const queue: string[] = [startId];
    const result: GraphNode[] = [];

    while (queue.length > 0) {
      const current = queue.shift()!;
      if (visited.has(current)) continue;
      visited.add(current);
      const node = this.nodes.get(current);
      if (node) result.push(node);
      const neighbors = this.adjacencyList.get(current) || [];
      for (const n of neighbors) {
        if (!visited.has(n)) queue.push(n);
      }
    }
    return result;
  }

  dfs(startId: string): GraphNode[] {
    const visited = new Set<string>();
    const stack: string[] = [startId];
    const result: GraphNode[] = [];

    while (stack.length > 0) {
      const current = stack.pop()!;
      if (visited.has(current)) continue;
      visited.add(current);
      const node = this.nodes.get(current);
      if (node) result.push(node);
      const neighbors = this.adjacencyList.get(current) || [];
      for (const n of neighbors) {
        if (!visited.has(n)) stack.push(n);
      }
    }
    return result;
  }

  shortestPath(from: string, to: string): string[] | null {
    if (!this.nodes.has(from) || !this.nodes.has(to)) return null;
    if (from === to) return [from];

    const visited = new Set<string>([from]);
    const queue: string[][] = [[from]];

    while (queue.length > 0) {
      const path = queue.shift()!;
      const current = path[path.length - 1];
      const neighbors = this.adjacencyList.get(current) || [];

      for (const neighbor of neighbors) {
        if (!visited.has(neighbor)) {
          const newPath = [...path, neighbor];
          if (neighbor === to) return newPath;
          visited.add(neighbor);
          queue.push(newPath);
        }
      }
    }
    return null;
  }

  // ─── Serialization ───────────────────────────────

  toJSON(): KnowledgeGraph {
    return {
      nodes: this.nodes,
      edges: this.edges,
      metadata: this.metadata,
    };
  }

  static fromJSON(data: KnowledgeGraph): Graph {
    const graph = new Graph(data.metadata.name, data.metadata.version);
    for (const [, node] of data.nodes) {
      graph.addNode(node);
    }
    for (const edge of data.edges) {
      graph.addEdge(edge);
    }
    return graph;
  }
}
