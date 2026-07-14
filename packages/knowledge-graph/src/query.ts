// SPDX-License-Identifier: MIT

import type { Graph } from './graph.js';
import type { GraphNode, ProductNode, BrandNode, SceneNode, MaterialNode } from './types.js';

export interface ProductQuery {
  brandId?: string;
  categoryId?: string;
  materialType?: string;
  colorFamily?: string;
  sceneStyle?: string;
  maxResults?: number;
}

export interface BrandQuery {
  style?: string;
  positioning?: string;
}

export interface SceneRecommendQuery {
  productId: string;
  materialIds?: string[];
  colorHex?: string;
  maxResults?: number;
}

export class QueryEngine {
  constructor(private graph: Graph) {}

  queryProducts(query: ProductQuery): ProductNode[] {
    const maxResults = query.maxResults ?? 20;
    let products = this.graph.findNodesByType('product') as ProductNode[];

    if (query.brandId) {
      const brandProducts = this._getRelatedProducts('brand', query.brandId);
      products = products.filter(p => brandProducts.has(p.id));
    }

    if (query.categoryId) {
      products = products.filter(p => p.properties.categoryId === query.categoryId);
    }

    if (query.materialType) {
      products = products.filter(p =>
        p.properties.materials?.some((m: string) =>
          m.toLowerCase().includes(query.materialType!.toLowerCase()),
        ),
      );
    }

    if (query.colorFamily) {
      products = products.filter(p =>
        p.properties.color?.toLowerCase().includes(query.colorFamily!.toLowerCase()),
      );
    }

    return products.slice(0, maxResults);
  }

  queryBrands(query: BrandQuery): BrandNode[] {
    let brands = this.graph.findNodesByType('brand') as BrandNode[];

    if (query.style) {
      brands = brands.filter(b =>
        b.properties.style?.some((s: string) =>
          s.toLowerCase().includes(query.style!.toLowerCase()),
        ),
      );
    }

    return brands;
  }

  recommendScenes(query: SceneRecommendQuery): SceneNode[] {
    const maxResults = query.maxResults ?? 5;
    const scenes = this.graph.findNodesByType('scene') as SceneNode[];

    const product = this.graph.getNode(query.productId);
    if (!product) return scenes.slice(0, maxResults);

    // Score scenes by compatibility with the product
    const scored = scenes.map(scene => {
      let score = 0;
      const productStyle = (product as any).properties?.style;
      const sceneStyle = scene.properties?.style;

      if (productStyle && sceneStyle && productStyle === sceneStyle) score += 3;

      if (query.colorHex && scene.properties?.colorPalette) {
        if (scene.properties.colorPalette.includes(query.colorHex)) score += 2;
      }

      return { scene, score };
    });

    return scored
      .sort((a, b) => b.score - a.score)
      .slice(0, maxResults)
      .map(s => s.scene);
  }

  private _getRelatedProducts(nodeType: string, nodeId: string): Set<string> {
    const ids = new Set<string>();
    const edges = this.graph.getEdges(nodeId);
    for (const edge of edges) {
      const otherId = edge.source === nodeId ? edge.target : edge.source;
      const otherNode = this.graph.getNode(otherId);
      if (otherNode?.type === 'product') {
        ids.add(otherId);
      }
    }
    return ids;
  }
}
