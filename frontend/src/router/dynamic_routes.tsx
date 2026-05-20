import { lazy, type ComponentType } from 'react';
import type { RouteObject } from 'react-router-dom';
import type { UserMenu } from '@/types/menu';

/**
 * Recursively convert a user menu tree to react-router RouteObject[].
 *
 * - Each menu with a component path generates a lazy-loaded route
 * - Hidden menus (hidden=true) still generate routes (just not shown in sidebar)
 * - External links (is_external_link=true) don't generate routes
 */
function menuToRoute(menu: UserMenu): RouteObject | null {
  // External links don't generate routes
  if (menu.is_external_link) {
    return null;
  }

  // Build the route object
  const route: RouteObject = {
    path: menu.route_path ?? undefined,
  };

  // If the menu has a component, lazy-load it
  if (menu.component) {
    // Normalize component path: ensure it doesn't start with '/'
    const compPath = menu.component.startsWith('/')
      ? menu.component.slice(1)
      : menu.component;

    const LazyComponent = lazy(
      () =>
        import(
          /* @vite-ignore */
          `@/pages/${compPath}`
        ) as Promise<{ default: ComponentType }>,
    );

    route.element = <LazyComponent />;
  }

  // Process children recursively
  if (menu.children && menu.children.length > 0) {
    const childRoutes = menu.children
      .map(menuToRoute)
      .filter(Boolean) as RouteObject[];

    if (childRoutes.length > 0) {
      route.children = childRoutes;
    }
  }

  return route;
}

/**
 * Generate RouteObject[] from a user menu tree.
 * Pass to `useRoutes()` to generate dynamic routes.
 */
export function generateRoutes(userMenus: UserMenu[]): RouteObject[] {
  return userMenus
    .map(menuToRoute)
    .filter(Boolean) as RouteObject[];
}
