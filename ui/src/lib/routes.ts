export type Route =
  | 'home'
  | 'foods'
  | 'profile'
  | 'settings'
  | 'nightReview'
  | 'history'
  | 'trends'
  | 'gallery';

export function parseRoute(hash: string): Route {
  const raw = hash.replace(/^#/, '') || '/';
  const path = raw.split('?')[0];
  if (path.startsWith('/gallery')) return 'gallery';
  if (path.startsWith('/night-review')) return 'nightReview';
  if (path.startsWith('/history')) return 'history';
  if (path.startsWith('/trends')) return 'trends';
  if (path.startsWith('/foods')) return 'foods';
  if (path.startsWith('/profile')) return 'profile';
  if (path.startsWith('/settings')) return 'settings';
  return 'home';
}

export function parseHashQuery(hash: string): URLSearchParams {
  const q = hash.includes('?') ? hash.split('?')[1] : '';
  return new URLSearchParams(q);
}

export function routeHref(route: Route): string {
  if (route === 'gallery') return '#/gallery';
  if (route === 'nightReview') return '#/night-review';
  if (route === 'history') return '#/history';
  if (route === 'trends') return '#/trends';
  if (route === 'foods') return '#/foods';
  if (route === 'profile') return '#/profile';
  if (route === 'settings') return '#/settings';
  return '#/';
}

export const isDevGalleryEnabled = import.meta.env.DEV;
