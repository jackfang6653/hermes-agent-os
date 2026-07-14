// SPDX-License-Identifier: MIT

import type { PageRoute } from './types';

export const ROUTES: PageRoute[] = [
  { path: '/', name: 'Dashboard', icon: 'layout-dashboard', component: 'Dashboard' },
  { path: '/projects', name: 'Projects', icon: 'folder', component: 'ProjectList' },
  { path: '/projects/:id', name: 'Project Detail', icon: 'folder-open', component: 'ProjectDetail' },
  { path: '/brands', name: 'Brands', icon: 'palette', component: 'BrandList' },
  { path: '/brands/:id', name: 'Brand Detail', icon: 'palette', component: 'BrandDetail' },
  { path: '/workflow', name: 'Workflow', icon: 'workflow', component: 'WorkflowEditor' },
  { path: '/assets', name: 'Assets', icon: 'image', component: 'AssetManager' },
  { path: '/settings', name: 'Settings', icon: 'settings', component: 'Settings' },
];

export const SIDEBAR_ROUTES = ROUTES.filter(r => r.name !== 'Project Detail' && r.name !== 'Brand Detail');

export function findRoute(path: string): PageRoute | undefined {
  return ROUTES.find(r => {
    const pattern = r.path.replace(/:id/g, '[^/]+');
    return new RegExp(`^${pattern}$`).test(path);
  });
}
