import { waitForBridge } from '@/lib/bridge';

export type MacroTargets = {
  energy_kcal: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
};

export type UserProfile = {
  onboarding_completed: boolean;
  age_years?: number;
  sex?: 'male' | 'female';
  height_cm?: number;
  weight_kg?: number;
  activity_level?: string;
  goal?: string;
  calorie_tolerance_pct?: number;
  use_split_day_targets?: boolean;
  gym_weekdays?: number[];
  macro_targets?: Record<string, MacroTargets>;
  micronutrient_targets?: Record<string, { target_value: number; unit: string }>;
  disclaimer?: string;
};

export type MetabolicPlan = {
  bmr_kcal: number;
  tdee_kcal: number;
  suggested_default: MacroTargets;
  suggested_gym: MacroTargets;
  suggested_rest: MacroTargets;
  warnings: string[];
  disclaimer: string;
};

export type EnergyBalance = {
  status: 'DEFICIT' | 'ON_TARGET' | 'SURPLUS' | null;
  energy_delta_kcal: number | null;
  tolerance_pct: number;
  tolerance_kcal: number | null;
  target_day_kind?: string;
};

function api() {
  return window.pywebview?.api;
}

export async function ensureProfileBridge(): Promise<boolean> {
  return waitForBridge();
}

export async function getUserProfile(): Promise<UserProfile> {
  const a = api();
  if (a?.get_user_profile) {
    return a.get_user_profile() as Promise<UserProfile>;
  }
  return { onboarding_completed: false };
}

export async function previewMetabolicPlan(payload: Record<string, unknown>): Promise<MetabolicPlan> {
  const a = api();
  if (a?.preview_metabolic_plan) {
    return a.preview_metabolic_plan(payload) as Promise<MetabolicPlan>;
  }
  throw new Error('Profile bridge unavailable');
}

export async function completeOnboarding(payload: Record<string, unknown>): Promise<UserProfile> {
  const a = api();
  if (a?.complete_onboarding) {
    return a.complete_onboarding(payload) as Promise<UserProfile>;
  }
  throw new Error('Profile bridge unavailable');
}

export async function quickStartTracking(): Promise<UserProfile> {
  const a = api();
  if (a?.quick_start_tracking) {
    return a.quick_start_tracking() as Promise<UserProfile>;
  }
  throw new Error('Profile bridge unavailable');
}
