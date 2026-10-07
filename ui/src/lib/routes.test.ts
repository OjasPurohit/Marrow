import { describe, expect, it } from 'vitest';
import { parseRoute, routeHref } from './routes';

describe('routes', () => {
  it('parses home', () => {
    expect(parseRoute('')).toBe('home');
    expect(parseRoute('#/')).toBe('home');
  });

  it('parses gallery', () => {
    expect(parseRoute('#/gallery')).toBe('gallery');
  });

  it('builds hrefs', () => {
    expect(routeHref('gallery')).toBe('#/gallery');
    expect(routeHref('home')).toBe('#/');
  });
});
