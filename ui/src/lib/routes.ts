export type Route = 'home' | 'foods' | 'profile' | 'gallery';

export function parseRoute(hash: string): Route {
  const path = hash.replace(/^#/, '') || '/';
  if (path.startsWith('/gallery')) return 'gallery';
  if (path.startsWith('/foods')) return 'foods';
  if (path.startsWith('/profile')) return 'profile';
  return 'home';
}

export function routeHref(route: Route): string {
  if (route === 'gallery') return '#/gallery';
  if (route === 'foods') return '#/foods';
  if (route === 'profile') return '#/profile';
  return '#/';
}

export const isDevGalleryEnabled = import.meta.env.DEV;
