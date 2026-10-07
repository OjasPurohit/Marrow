import { describe, expect, it } from 'vitest';
import { confidenceLabel, formatAmount, formatKcal } from './parseQuantity';

describe('parseQuantity helpers', () => {
  it('formats kcal without coercing null to zero', () => {
    expect(formatKcal(null)).toBe('—');
    expect(formatKcal(undefined)).toBe('—');
    expect(formatKcal(142.4)).toBe('142');
  });

  it('formats amounts', () => {
    expect(formatAmount(2)).toBe('2');
    expect(formatAmount(1.5)).toBe('1.5');
  });

  it('maps confidence labels', () => {
    expect(confidenceLabel('EXACT')).toBe('Exact');
    expect(confidenceLabel('GOOD')).toBe('Good');
    expect(confidenceLabel('ESTIMATED')).toBe('Estimated');
  });
});
