import { waitForBridge } from '@/lib/bridge';

export type TrendRange = 7 | 30 | 90;

export type WeeklyBalanceRow = {
  week_start: string;
  days_logged: number;
  avg_energy_delta_kcal: number | null;
  cumulative_balance_kcal: number | null;
};

export type TrendSeriesPayload = {
  range_days: TrendRange;
  start_date: string;
  end_date: string;
  dates: string[];
  energy_kcal: (number | null)[];
  protein_g: (number | null)[];
  energy_delta_kcal: (number | null)[];
  rolling_7_energy_kcal: (number | null)[];
  rolling_7_balance_kcal: (number | null)[];
  micronutrients: Record<string, (number | null)[]>;
  micronutrient_keys: string[];
  weight_kg: (number | null)[];
  weight_smooth_kg: (number | null)[];
  weekly_balance: WeeklyBalanceRow[];
  days_logged: number;
};

export type WeightEntry = {
  id: number;
  logged_date: string;
  weight_kg: number;
  note: string | null;
  created_at: string;
  smooth_kg?: number | null;
};

async function api() {
  await waitForBridge();
  const bridge = window.pywebview?.api as Record<string, unknown> | undefined;
  if (!bridge) throw new Error('Bridge unavailable');
  return bridge;
}

export async function getTrendSeries(
  rangeDays: TrendRange,
  micronutrientKeys?: string[],
): Promise<TrendSeriesPayload> {
  const bridge = await api();
  const fn = bridge.get_trend_series as (
    days: number,
    keys?: string[],
  ) => Promise<TrendSeriesPayload>;
  return fn(rangeDays, micronutrientKeys);
}

export async function getWeightLogWithTrend(limit = 90): Promise<{
  entries: WeightEntry[];
  window_days: number;
}> {
  const bridge = await api();
  const fn = bridge.get_weight_log_with_trend as (n: number) => Promise<{
    entries: WeightEntry[];
    window_days: number;
  }>;
  return fn(limit);
}

export async function addWeightEntry(payload: {
  weight_kg: number;
  logged_date?: string;
  note?: string;
}): Promise<WeightEntry> {
  const bridge = await api();
  const fn = bridge.add_weight_entry as (p: typeof payload) => Promise<WeightEntry>;
  return fn(payload);
}

export async function deleteWeightEntry(entryId: number): Promise<void> {
  const bridge = await api();
  const fn = bridge.delete_weight_entry as (id: number) => Promise<{ deleted: boolean }>;
  await fn(entryId);
}
