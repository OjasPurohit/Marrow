/// <reference types="svelte" />
/// <reference types="vite/client" />

interface PyWebViewApi {
  ping(): Promise<string>;
  get_app_info(): Promise<Record<string, unknown>>;
  get_window_geometry(): Promise<{ x: number; y: number; width: number; height: number }>;
  save_window_geometry(x: number, y: number, width: number, height: number): Promise<boolean>;
}

interface PyWebView {
  api: PyWebViewApi;
}

declare global {
  interface Window {
    pywebview?: PyWebView;
  }
}

export {};
