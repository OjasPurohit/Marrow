/** Food search helpers and bridge wrappers. */

import { waitForBridge } from '@/lib/bridge';

export type FoodSearchResult = {
  id: number;
  name: string;
  source: string;
  brand: string | null;
  basis: string;
  preparation: string;
  data_quality: string;
  barcode: string | null;
  rank?: number;
};

export type FoodSearchResponse = {
  query: string;
  results: FoodSearchResult[];
  elapsed_ms: number;
};

const DEMO_RESULTS: FoodSearchResult[] = [
  {
    id: 1,
    name: 'Banana, raw',
    source: 'usda',
    brand: null,
    basis: 'per_100g',
    preparation: 'raw',
    data_quality: 'high',
    barcode: null,
  },
  {
    id: 2,
    name: 'Chicken breast, grilled',
    source: 'usda',
    brand: null,
    basis: 'per_100g',
    preparation: 'cooked',
    data_quality: 'high',
    barcode: null,
  },
];

export function filterDemoFoods(query: string): FoodSearchResult[] {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  return DEMO_RESULTS.filter((f) => f.name.toLowerCase().includes(q));
}

export async function searchFoods(query: string, limit = 25): Promise<FoodSearchResponse> {
  const api = window.pywebview?.api;
  if (api?.search_foods) {
    return api.search_foods(query, limit) as Promise<FoodSearchResponse>;
  }
  const results = filterDemoFoods(query).slice(0, limit);
  return { query, results, elapsed_ms: 0 };
}

export async function ensureFoodBridge(): Promise<boolean> {
  return waitForBridge();
}
