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
  decomposition?: {
    food_name: string;
    food_id: number | null;
    grams: number;
    energy_kcal: number | null;
  }[];
  recipe_cache_name?: string;
};

export type ParseFoodTextResponse = {
  input: string;
  meal_tag: string;
  items: ParseDraftItem[];
  parser: string;
  groq_available: boolean;
  groq_used: boolean;
};

export type DiaryNutrients = {
  energy_kcal: number | null;
  protein_g: number | null;
  carbs_g: number | null;
  fat_g: number | null;
};

export type EnergyBalance = {
  status: 'DEFICIT' | 'ON_TARGET' | 'SURPLUS' | null;
  energy_delta_kcal: number | null;
  tolerance_pct: number;
  tolerance_kcal: number | null;
  target_day_kind?: string;
};

export type DiaryTotals = DiaryNutrients & {
  entry_count: number;
  targets: Record<string, number>;
  remaining: DiaryNutrients;
  energy_balance?: EnergyBalance;
};

export type DiaryMealSection = {
  meal_tag: string;
  entries: DiaryEntry[];
  totals: DiaryNutrients;
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
  protein_g?: number | null;
  carbs_g?: number | null;
  fat_g?: number | null;
  match_confidence: string;
  raw_fragment: string | null;
  logged_at: string;
};

export type DiaryDayResponse = {
  log_date: string;
  entries: DiaryEntry[];
  meals: DiaryMealSection[];
  totals: DiaryTotals;
};

function api() {
  return window.pywebview?.api;
}

export async function ensureDiaryBridge(): Promise<boolean> {
  return waitForBridge();
}

export async function parseFoodPhoto(
  imageBase64: string,
  mealTag = 'snack',
  mimeType = 'image/jpeg',
): Promise<ParseFoodTextResponse> {
  const a = window.pywebview?.api;
  if (!a) throw new Error('Photo logging requires the desktop app');
  return (await a.parse_food_photo(imageBase64, mealTag, mimeType)) as ParseFoodTextResponse;
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
    food_id?: number;
    amount: number;
    unit: string;
    match_confidence: string;
    raw_fragment?: string;
    decomposition?: ParseDraftItem['decomposition'];
    recipe_cache_name?: string;
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
  const emptyNutrients: DiaryNutrients = {
    energy_kcal: null,
    protein_g: null,
    carbs_g: null,
    fat_g: null,
  };
  return {
    log_date: logDate ?? '',
    entries: [],
    meals: [],
    totals: {
      ...emptyNutrients,
      entry_count: 0,
      targets: {},
      remaining: emptyNutrients,
    },
  };
}

export async function getDailyNutrientTotals(logDate?: string): Promise<{
  log_date: string;
  totals: DiaryTotals;
  meals: DiaryMealSection[];
}> {
  const a = api();
  if (a?.get_daily_nutrient_totals) {
    return a.get_daily_nutrient_totals(logDate ?? null) as Promise<{
      log_date: string;
      totals: DiaryTotals;
      meals: DiaryMealSection[];
    }>;
  }
  const day = await listDiaryEntriesForDate(logDate);
  return { log_date: day.log_date, totals: day.totals, meals: day.meals };
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
