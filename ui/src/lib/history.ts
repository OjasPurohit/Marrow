import { waitForBridge } from '@/lib/bridge';

export type HistoryDay = {
  log_date: string;
  entry_count: number;
  logged: boolean;
  data_incomplete: boolean;
  energy_kcal: number | null;
  protein_g: number | null;
  energy_balance_status: string | null;
  energy_delta_kcal: number | null;
};

export type DiaryHistoryPayload = {
  start_date: string;
  end_date: string;
  year?: number;
  month?: number;
  days: HistoryDay[];
  days_logged: number;
  days_in_range: number;
  streak: { current: number; best_in_range: number };
};

async function api() {
  await waitForBridge();
  const bridge = window.pywebview?.api as Record<string, unknown> | undefined;
  if (!bridge) throw new Error('Bridge unavailable');
  return bridge;
}

export async function getDiaryHistoryMonth(year: number, month: number): Promise<DiaryHistoryPayload> {
  const bridge = await api();
  const fn = bridge.get_diary_history_month as (y: number, m: number) => Promise<DiaryHistoryPayload>;
  return fn(year, month);
}

export async function getDiaryHistoryRange(
  startDate: string,
  endDate: string,
): Promise<DiaryHistoryPayload> {
  const bridge = await api();
  const fn = bridge.get_diary_history_range as (s: string, e: string) => Promise<DiaryHistoryPayload>;
  return fn(startDate, endDate);
}
