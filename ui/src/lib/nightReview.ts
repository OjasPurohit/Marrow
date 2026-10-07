import { waitForBridge } from '@/lib/bridge';
import type { EnergyBalance } from '@/lib/diary';

export type NutrientContributor = {
  food_name: string;
  food_id: number;
  entry_id?: number;
  amount: number;
  unit: string;
};

export type NightReviewNutrientRow = {
  key: string;
  label: string;
  unit: string;
  consumed: number | null;
  target: number | null;
  pct_of_target: number | null;
  status: 'no_data' | 'ok';
  flag: 'low' | 'high' | null;
  coverage: { with_data: number; missing: number };
  partial_total: boolean;
  top_contributors: NutrientContributor[];
};

export type NightReviewResponse = {
  log_date: string;
  entry_count: number;
  energy_balance: EnergyBalance;
  macro_totals: Record<string, number | null>;
  targets: Record<string, number>;
  nutrients: NightReviewNutrientRow[];
  flagged: NightReviewNutrientRow[];
  macro_split: {
    protein_pct: number | null;
    carbs_pct: number | null;
    fat_pct: number | null;
  };
  estimated_confidence: {
    estimated_kcal: number;
    known_kcal: number | null;
    estimated_pct_of_known: number | null;
  };
  summary_lines: string[];
  groq_summary: string | null;
};

export async function ensureNightReviewBridge(): Promise<void> {
  await waitForBridge();
}

export async function getNightReview(logDate?: string): Promise<NightReviewResponse> {
  await ensureNightReviewBridge();
  const api = window.pywebview?.api;
  if (!api?.get_night_review) {
    throw new Error('Night review bridge unavailable');
  }
  return api.get_night_review(logDate) as Promise<NightReviewResponse>;
}
