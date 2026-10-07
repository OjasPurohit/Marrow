export type Route = 'home' | 'gallery';

export function parseRoute(hash: string): Route {
  const path = hash.replace(/^#/, '') || '/';
  if (path.startsWith('/gallery')) return 'gallery';
  return 'home';
}

export function routeHref(route: Route): string {
  return route === 'gallery' ? '#/gallery' : '#/';
}

export const isDevGalleryEnabled = import.meta.env.DEV;
