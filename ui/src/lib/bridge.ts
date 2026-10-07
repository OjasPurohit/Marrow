/** Typed access to pywebview bridge with browser fallback for dev. */

export type AppInfo = {
  name: string;
  version: string;
  platform: string;
  python: string;
  data_dir: string;
  database_path: string;
  schema_version: number;
  is_dev: boolean;
};

function api() {
  return window.pywebview?.api;
}

export async function waitForBridge(timeoutMs = 8000): Promise<boolean> {
  if (api()) return true;
  return new Promise((resolve) => {
    const start = Date.now();
    const tick = () => {
      if (api()) {
        resolve(true);
        return;
      }
      if (Date.now() - start > timeoutMs) {
        resolve(false);
        return;
      }
      requestAnimationFrame(tick);
    };
    tick();
  });
}

export async function ping(): Promise<string> {
  const a = api();
  if (a) return a.ping();
  return 'browser';
}

export async function getAppInfo(): Promise<AppInfo> {
  const a = api();
  if (a) return a.get_app_info() as Promise<AppInfo>;
  return {
    name: 'Marrow',
    version: '0.1.0-dev',
    platform: 'browser',
    python: '—',
    data_dir: '—',
    database_path: '—',
    schema_version: 0,
    is_dev: true,
  };
}

export function isPyWebView(): boolean {
  return Boolean(api());
}
