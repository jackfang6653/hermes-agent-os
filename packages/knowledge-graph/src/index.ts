// SPDX-License-Identifier: MIT
export type { GraphNode, GraphEdge, KnowledgeGraph, NodeType, RelationshipType } from './types.js';
export type {
  BrandNode,
  CategoryNode,
  ProductNode,
  SceneNode,
  MaterialNode,
  ColorNode,
  StyleNode,
} from './types.js';
export { Graph } from './graph.js';
export { QueryEngine } from './query.js';
export type { ProductQuery, BrandQuery, SceneRecommendQuery } from './query.js';
export const VERSION = '1.0.0';
