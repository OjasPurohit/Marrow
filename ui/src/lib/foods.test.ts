import { describe, expect, it } from 'vitest';
import { filterDemoFoods } from '@/lib/foods';

describe('filterDemoFoods', () => {
  it('returns empty for blank query', () => {
    expect(filterDemoFoods('')).toEqual([]);
  });

  it('matches case-insensitive substring', () => {
    const hits = filterDemoFoods('ban');
    expect(hits.some((h) => h.name.includes('Banana'))).toBe(true);
  });
});
