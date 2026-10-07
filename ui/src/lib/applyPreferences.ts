import type { UserSettings } from '@/lib/settings';

const SCALE_MAP: Record<UserSettings['ui_scale'], string> = {
  '0.875': '0_875',
  '1': '1',
  '1.125': '1_125',
  '1.25': '1_25',
};

export function applyUserSettings(settings: UserSettings) {
  const root = document.documentElement;
  if (settings.theme === 'system') {
    delete root.dataset.theme;
  } else {
    root.dataset.theme = settings.theme;
  }
  root.dataset.uiScale = SCALE_MAP[settings.ui_scale] ?? '1';
  root.dataset.reducedMotion = settings.reduced_motion ? 'true' : 'false';
  root.dataset.reducedTransparency = settings.reduced_transparency ? 'true' : 'false';
  root.dataset.higherContrast = settings.higher_contrast ? 'true' : 'false';
  root.dataset.units = settings.units;
}
