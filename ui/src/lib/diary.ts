import { waitForBridge } from '@/lib/bridge';
import { searchFoods, type FoodSearchResult } from '@/lib/foods';

export type ParseDraftItem = {
  draft_id: string;
  raw_fragment: string;
  amount: number;
  unit: string;
  food_query: string;
  food_id: number | null;
  food_name: string | null;
  match_confidence: string;
  energy_kcal: number | null;
  nutrients: Record<string, number | null>;
  grams_equivalent: number | null;
  warnings: string[];
  conversion_note?: string | null;
  alternatives?: { id: number; name: string; rank?: number }[];
};

export type ParseFoodTextResponse = {
  input: string;
  meal_tag: string;
  items: ParseDraftItem[];
  parser: string;
  groq_available: boolean;
  groq_used: boolean;
};

export type DiaryEntry = {
  entry_id: number;
  log_id: number;
  meal_tag: string;
  food_id: number;
  food_name: string;
  amount: number;
  unit: string;
  grams_equivalent: number;
  energy_kcal: number | null;
  match_confidence: string;
  raw_fragment: string | null;
  logged_at: string;
};

export type DiaryDayResponse = {
  log_date: string;
  entries: DiaryEntry[];
  totals: { energy_kcal: number | null; entry_count: number };
};

function api() {
  return window.pywebview?.api;
}

export async function ensureDiaryBridge(): Promise<boolean> {
  return waitForBridge();
}

export async function parseFoodText(
  text: string,
  mealTag = 'snack',
): Promise<ParseFoodTextResponse> {
  const a = api();
  if (a?.parse_food_text) {
    return a.parse_food_text(text, mealTag) as Promise<ParseFoodTextResponse>;
  }
  return { input: text, meal_tag: mealTag, items: [], parser: 'none', groq_available: false, groq_used: false };
}

export async function confirmAndSaveLog(payload: {
  log_date?: string;
  meal_tag: string;
  source_text?: string;
  items: {
    food_id: number;
    amount: number;
    unit: string;
    match_confidence: string;
    raw_fragment?: string;
  }[];
}): Promise<{ log_id: number; entries: unknown[]; totals: { energy_kcal: number | null } }> {
  const a = api();
  if (a?.confirm_and_save_log) {
    return a.confirm_and_save_log(payload) as Promise<{
      log_id: number;
      entries: unknown[];
      totals: { energy_kcal: number | null };
    }>;
  }
  throw new Error('Diary bridge unavailable');
}

export async function listDiaryEntriesForDate(logDate?: string): Promise<DiaryDayResponse> {
  const a = api();
  if (a?.list_diary_entries_for_date) {
    return a.list_diary_entries_for_date(logDate ?? null) as Promise<DiaryDayResponse>;
  }
  return { log_date: logDate ?? '', entries: [], totals: { energy_kcal: null, entry_count: 0 } };
}

export async function swapDraftFood(
  draft: ParseDraftItem,
  food: FoodSearchResult,
): Promise<ParseDraftItem> {
  const a = api();
  if (a?.convert_food_serving && a?.get_food_detail) {
    const converted = await a.convert_food_serving(
      food.id,
      draft.amount,
      draft.unit,
    ) as { amount: number; unit: string; grams_equivalent: number; nutrients: Record<string, number | null>; note?: string };
    return {
      ...draft,
      food_id: food.id,
      food_name: food.name,
      amount: converted.amount,
      unit: converted.unit,
      grams_equivalent: converted.grams_equivalent,
      energy_kcal: converted.nutrients.energy_kcal ?? null,
      nutrients: converted.nutrients,
      match_confidence: 'GOOD',
      conversion_note: converted.note ?? null,
    };
  }
  return { ...draft, food_id: food.id, food_name: food.name, match_confidence: 'GOOD' };
}

export async function searchFoodsForSwap(query: string) {
  return searchFoods(query, 8);
}
