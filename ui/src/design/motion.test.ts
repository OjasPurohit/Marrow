import { describe, expect, it } from 'vitest';
import { projectMomentum, rubberband } from './motion';

describe('motion helpers', () => {
  it('projects momentum forward', () => {
    const delta = projectMomentum(500);
    expect(delta).toBeGreaterThan(0);
  });

  it('rubberbands with diminishing returns', () => {
    const small = rubberband(10, 400);
    const large = rubberband(100, 400);
    expect(large).toBeLessThan(100);
    expect(large / 100).toBeLessThan(small / 10);
  });
});
