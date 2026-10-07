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

  it('parses foods', () => {
    expect(parseRoute('#/foods')).toBe('foods');
  });

  it('parses profile', () => {
    expect(parseRoute('#/profile')).toBe('profile');
  });

  it('parses settings', () => {
    expect(parseRoute('#/settings')).toBe('settings');
  });

  it('parses night review', () => {
    expect(parseRoute('#/night-review')).toBe('nightReview');
    expect(parseRoute('#/night-review?date=2025-10-01')).toBe('nightReview');
  });

  it('parses history and trends', () => {
    expect(parseRoute('#/history')).toBe('history');
    expect(parseRoute('#/trends')).toBe('trends');
  });

  it('builds hrefs', () => {
    expect(routeHref('gallery')).toBe('#/gallery');
    expect(routeHref('nightReview')).toBe('#/night-review');
    expect(routeHref('history')).toBe('#/history');
    expect(routeHref('trends')).toBe('#/trends');
    expect(routeHref('foods')).toBe('#/foods');
    expect(routeHref('profile')).toBe('#/profile');
    expect(routeHref('settings')).toBe('#/settings');
    expect(routeHref('home')).toBe('#/');
  });
});
