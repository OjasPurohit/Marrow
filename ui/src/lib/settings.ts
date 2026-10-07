import { waitForBridge } from '@/lib/bridge';

export type UserSettings = {
  theme: 'system' | 'dark' | 'light';
  units: 'metric' | 'imperial';
  ui_scale: '0.875' | '1' | '1.125' | '1.25';
  reduced_motion: boolean;
  reduced_transparency: boolean;
  higher_contrast: boolean;
};

export type GroqSettings = {
  chat_model: string;
  vision_model: string;
  whisper_model: string;
  request_timeout_sec: number;
  max_retries: number;
  enable_night_summary: boolean;
  enable_voice_hotkey: boolean;
  enable_photo_parse: boolean;
  voice_hotkey: string;
  voice_record_seconds: number;
  configured: boolean;
};

export type DataSyncStatus = {
  mode: string;
  full_sync_available: boolean;
  summary: string;
  sync_state: string;
  catalog_food_count: number;
  needs_seed: boolean;
};

export type BackupInfo = {
  filename: string;
  path: string;
  size_bytes: number;
  modified_at: string;
};

const defaultSettings: UserSettings = {
  theme: 'system',
  units: 'metric',
  ui_scale: '1',
  reduced_motion: false,
  reduced_transparency: false,
  higher_contrast: false,
};

function api() {
  return window.pywebview?.api;
}

export async function ensureSettingsBridge(): Promise<boolean> {
  return waitForBridge();
}

export async function getUserSettings(): Promise<UserSettings> {
  const a = api();
  if (a) return (await a.get_user_settings()) as UserSettings;
  return defaultSettings;
}

export async function updateUserSettings(patch: Partial<UserSettings>): Promise<UserSettings> {
  const a = api();
  if (a) return (await a.update_user_settings(patch)) as UserSettings;
  return { ...defaultSettings, ...patch };
}

export async function getGroqSettings(): Promise<GroqSettings> {
  const a = api();
  if (a) return (await a.get_groq_settings()) as GroqSettings;
  return {
    chat_model: 'llama-3.3-70b-versatile',
    vision_model: 'llama-3.2-11b-vision-preview',
    whisper_model: 'whisper-large-v3',
    request_timeout_sec: 30,
    max_retries: 2,
    enable_night_summary: true,
    enable_voice_hotkey: true,
    enable_photo_parse: true,
    voice_hotkey: 'ctrl+shift+v',
    voice_record_seconds: 8,
    configured: false,
  };
}

export async function updateGroqSettings(patch: Partial<GroqSettings>): Promise<GroqSettings> {
  const a = api();
  if (a) return (await a.update_groq_settings(patch)) as GroqSettings;
  return await getGroqSettings();
}

export async function setGroqApiKey(key: string): Promise<GroqSettings> {
  const a = api();
  if (!a) throw new Error('Bridge unavailable');
  return (await a.set_groq_api_key(key)) as GroqSettings;
}

export async function clearGroqApiKey(): Promise<GroqSettings> {
  const a = api();
  if (!a) throw new Error('Bridge unavailable');
  return (await a.clear_groq_api_key()) as GroqSettings;
}

export async function getDataSyncStatus(): Promise<DataSyncStatus> {
  const a = api();
  if (a) return (await a.get_data_sync_status()) as DataSyncStatus;
  return {
    mode: 'bundled_catalog',
    full_sync_available: false,
    summary: 'Browser preview — sync status available in the desktop app.',
    sync_state: 'unknown',
    catalog_food_count: 0,
    needs_seed: false,
  };
}

export async function listBackups(): Promise<BackupInfo[]> {
  const a = api();
  if (a) return (await a.list_backups()) as BackupInfo[];
  return [];
}

export async function createBackup(): Promise<BackupInfo> {
  const a = api();
  if (!a) throw new Error('Bridge unavailable');
  return (await a.create_backup()) as BackupInfo;
}

export async function restoreBackup(filename: string): Promise<void> {
  const a = api();
  if (!a) throw new Error('Bridge unavailable');
  await a.restore_backup(filename);
}

export async function exportUserDataJson(): Promise<string> {
  const a = api();
  if (!a) throw new Error('Bridge unavailable');
  return (await a.export_user_data_json()) as string;
}

export async function exportDiaryCsv(): Promise<string> {
  const a = api();
  if (!a) throw new Error('Bridge unavailable');
  return (await a.export_diary_csv()) as string;
}

export async function importUserDataJson(jsonText: string): Promise<Record<string, number>> {
  const a = api();
  if (!a) throw new Error('Bridge unavailable');
  return (await a.import_user_data_json(jsonText)) as Record<string, number>;
}

export async function importDiaryCsv(csvText: string): Promise<Record<string, number>> {
  const a = api();
  if (!a) throw new Error('Bridge unavailable');
  return (await a.import_diary_csv(csvText)) as Record<string, number>;
}

export function downloadTextFile(filename: string, content: string, mime = 'text/plain') {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
