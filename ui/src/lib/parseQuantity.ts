/** Display helpers for parsed quantities (mirrors Python parser semantics). */

export function formatKcal(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  return `${Math.round(value)}`;
}

export function formatGrams(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  if (Math.abs(value - Math.round(value)) < 0.05) return `${Math.round(value)}g`;
  return `${value.toFixed(1)}g`;
}

export function formatAmount(amount: number): string {
  if (Number.isInteger(amount)) return String(amount);
  return amount.toFixed(2).replace(/\.?0+$/, '');
}

export function confidenceLabel(level: string): string {
  switch (level) {
    case 'EXACT':
      return 'Exact';
    case 'GOOD':
      return 'Good';
    default:
      return 'Estimated';
  }
}
