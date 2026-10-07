import { waitForBridge } from '@/lib/bridge';

export type WeeklyNutritionAverage = {
  window_days: number;
  start_date: string;
  end_date: string;
  days_logged: number;
  days_remaining: number;
  eligible: boolean;
  macros_avg: Record<string, number | null>;
  micros_avg: Record<string, number | null>;
  micro_labels: Record<string, string>;
};

function api() {
  return window.pywebview?.api;
}

export async function ensureWeeklyBridge(): Promise<boolean> {
  return waitForBridge();
}

export async function getWeeklyNutritionAverage(): Promise<WeeklyNutritionAverage> {
  const a = api();
  if (a?.get_weekly_nutrition_average) {
    return a.get_weekly_nutrition_average() as Promise<WeeklyNutritionAverage>;
  }
  return {
    window_days: 7,
    start_date: '',
    end_date: '',
    days_logged: 0,
    days_remaining: 7,
    eligible: false,
    macros_avg: {},
    micros_avg: {},
    micro_labels: {},
  };
}
