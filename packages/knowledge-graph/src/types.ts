// SPDX-License-Identifier: MIT

// ─── Node Types ──────────────────────────────────────────

export type NodeType =
  | 'brand'
  | 'category'
  | 'product'
  | 'scene'
  | 'material'
  | 'style'
  | 'color'
  | 'attribute';

export type RelationshipType =
  | 'BELONGS_TO'
  | 'HAS_STYLE'
  | 'USES_MATERIAL'
  | 'COMPOSED_OF'
  | 'INSPIRED_BY'
  | 'HAS_COLOR'
  | 'SIMILAR_TO'
  | 'RECOMMENDS'
  | 'CONTAINS'
  | 'RELATED';

// ─── Nodes ───────────────────────────────────────────────

export interface GraphNode<T = Record<string, unknown>> {
  id: string;
  type: NodeType;
  label: string;
  properties: T;
  metadata: {
    createdAt: string;
    updatedAt: string;
    source?: string;
    confidence?: number;
  };
}

export type BrandNode = GraphNode<{
  name: string;
  style: string[];
  positioning: string[];
}>;

export type CategoryNode = GraphNode<{
  name: string;
  path: string;
  level: number;
}>;

export type ProductNode = GraphNode<{
  sku: string;
  brandId: string;
  categoryId: string;
  dimensions: string;
  materials: string[];
  color: string;
  status: string;
}>;

export type SceneNode = GraphNode<{
  style: string;
  moodKeywords: string[];
  colorPalette: string[];
}>;

export type MaterialNode = GraphNode<{
  type: string;
  category: string;
  texture: string;
  sustainability: boolean;
}>;

export type ColorNode = GraphNode<{
  hex: string;
  family: string;
  name: string;
}>;

export type StyleNode = GraphNode<{
  name: string;
  origin: string;
  era: string;
  keywords: string[];
}>;

// ─── Edges ───────────────────────────────────────────────

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationship: RelationshipType;
  weight: number;
  properties: Record<string, unknown>;
}

// ─── Graph ───────────────────────────────────────────────

export interface KnowledgeGraph {
  nodes: Map<string, GraphNode>;
  edges: GraphEdge[];
  metadata: {
    name: string;
    version: string;
    nodeCount: number;
    edgeCount: number;
  };
}
