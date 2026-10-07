<script lang="ts">
  import { onMount } from 'svelte';
  import Button from '@/components/Button.svelte';
  import Card from '@/components/Card.svelte';
  import { getAppInfo, type AppInfo } from '@/lib/bridge';
  import { applyUserSettings } from '@/lib/applyPreferences';
  import {
    clearGroqApiKey,
    createBackup,
    downloadTextFile,
    ensureSettingsBridge,
    exportDiaryCsv,
    exportUserDataJson,
    getDataSyncStatus,
    getGroqSettings,
    getUserSettings,
    importDiaryCsv,
    importUserDataJson,
    listBackups,
    restoreBackup,
    setGroqApiKey,
    updateGroqSettings,
    updateUserSettings,
    type BackupInfo,
    type DataSyncStatus,
    type GroqSettings,
    type UserSettings,
  } from '@/lib/settings';

  let settings = $state<UserSettings | null>(null);
  let groq = $state<GroqSettings | null>(null);
  let sync = $state<DataSyncStatus | null>(null);
  let backups = $state<BackupInfo[]>([]);
  let groqKeyInput = $state('');
  let status = $state<string | null>(null);
  let error = $state<string | null>(null);
  let busy = $state(false);
  let appInfo = $state<AppInfo | null>(null);

  async function refresh() {
    await ensureSettingsBridge();
    settings = await getUserSettings();
    groq = await getGroqSettings();
    sync = await getDataSyncStatus();
    backups = await listBackups();
    appInfo = await getAppInfo();
    if (settings) applyUserSettings(settings);
  }

  onMount(() => {
    void refresh();
  });

  async function saveSettings(patch: Partial<UserSettings>) {
    if (!settings) return;
    settings = await updateUserSettings(patch);
    applyUserSettings(settings);
    status = 'Preferences saved';
  }

  async function saveGroq(patch: Partial<GroqSettings>) {
    groq = await updateGroqSettings(patch);
    status = 'Groq settings updated';
  }

  async function handleGroqKey() {
    error = null;
    try {
      if (!groqKeyInput.trim()) {
        groq = await clearGroqApiKey();
      } else {
        groq = await setGroqApiKey(groqKeyInput.trim());
        groqKeyInput = '';
      }
      status = 'Groq API key updated';
    } catch (e) {
      error = e instanceof Error ? e.message : 'Key update failed';
    }
  }

  async function handleBackupNow() {
    busy = true;
    error = null;
    try {
      await createBackup();
      backups = await listBackups();
      status = 'Backup created';
    } catch (e) {
      error = e instanceof Error ? e.message : 'Backup failed';
    } finally {
      busy = false;
    }
  }

  async function handleRestore(filename: string) {
    if (!confirm(`Restore ${filename}? Current data will be replaced.`)) return;
    busy = true;
    try {
      await restoreBackup(filename);
      status = 'Database restored — reload the app to refresh all screens.';
    } catch (e) {
      error = e instanceof Error ? e.message : 'Restore failed';
    } finally {
      busy = false;
    }
  }

  async function handleExportJson() {
    try {
      const text = await exportUserDataJson();
      downloadTextFile(`marrow-export-${new Date().toISOString().slice(0, 10)}.json`, text, 'application/json');
    } catch (e) {
      error = e instanceof Error ? e.message : 'Export failed';
    }
  }

  async function handleExportCsv() {
    try {
      const text = await exportDiaryCsv();
      downloadTextFile(`marrow-diary-${new Date().toISOString().slice(0, 10)}.csv`, text, 'text/csv');
    } catch (e) {
      error = e instanceof Error ? e.message : 'Export failed';
    }
  }

  async function onImportJson(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    const text = await file.text();
    try {
      const stats = await importUserDataJson(text);
      status = `Imported JSON — ${stats.diary_entries ?? 0} diary entries`;
      await refresh();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Import failed';
    } finally {
      input.value = '';
    }
  }

  async function onImportCsv(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    const text = await file.text();
    try {
      const stats = await importDiaryCsv(text);
      status = `Imported CSV — ${stats.diary_entries ?? 0} entries`;
    } catch (e) {
      error = e instanceof Error ? e.message : 'Import failed';
    } finally {
      input.value = '';
    }
  }
</script>

<main class="settings">
  <h1 class="text-display">Settings</h1>
  <p class="text-body lede">Appearance, data safety, Groq, and keyboard shortcuts.</p>

  {#if error}
    <p class="banner error">{error}</p>
  {/if}
  {#if status}
    <p class="banner ok">{status}</p>
  {/if}

  {#if settings}
    <Card title="Profile & targets" subtitle="Onboarding and macro plan">
      <p class="text-body">
        Edit your plan on <a href="#/profile">Profile</a> or rerun onboarding from Today if you reset data.
      </p>
    </Card>

    <Card title="Appearance" subtitle="Theme, units, and UI scale">
      <div class="grid">
        <label>
          <span class="text-caption">Theme</span>
          <select
            value={settings.theme}
            onchange={(e) => saveSettings({ theme: (e.currentTarget as HTMLSelectElement).value as UserSettings['theme'] })}
          >
            <option value="system">System</option>
            <option value="dark">Dark</option>
            <option value="light">Light</option>
          </select>
        </label>
        <label>
          <span class="text-caption">Units</span>
          <select
            value={settings.units}
            onchange={(e) => saveSettings({ units: (e.currentTarget as HTMLSelectElement).value as UserSettings['units'] })}
          >
            <option value="metric">Metric (kg, g)</option>
            <option value="imperial">Imperial (lb, oz)</option>
          </select>
        </label>
        <label>
          <span class="text-caption">UI scale</span>
          <select
            value={settings.ui_scale}
            onchange={(e) =>
              saveSettings({ ui_scale: (e.currentTarget as HTMLSelectElement).value as UserSettings['ui_scale'] })}
          >
            <option value="0.875">Small</option>
            <option value="1">Default</option>
            <option value="1.125">Large</option>
            <option value="1.25">Extra large</option>
          </select>
        </label>
      </div>
    </Card>

    <Card title="Accessibility" subtitle="Overrides system preferences when enabled">
      <p class="text-caption">
        When reduced motion is off, Marrow still respects your OS “reduce motion” setting via CSS. Turn on the toggle below to force reduced motion in-app.
      </p>
      <div class="checks">
        <label><input type="checkbox" checked={settings.reduced_motion} onchange={(e) => saveSettings({ reduced_motion: e.currentTarget.checked })} /> Reduced motion</label>
        <label><input type="checkbox" checked={settings.reduced_transparency} onchange={(e) => saveSettings({ reduced_transparency: e.currentTarget.checked })} /> Reduced transparency</label>
        <label><input type="checkbox" checked={settings.higher_contrast} onchange={(e) => saveSettings({ higher_contrast: e.currentTarget.checked })} /> Higher contrast</label>
      </div>
    </Card>
  {/if}

  {#if groq}
    <Card title="Groq (optional)" subtitle="Stored in OS keyring — never in SQLite">
      <div class="grid">
        <label class="full">
          <span class="text-caption">API key</span>
          <input type="password" placeholder={groq.configured ? '•••••••• (configured)' : 'Paste API key'} bind:value={groqKeyInput} />
        </label>
        <Button variant="secondary" onclick={handleGroqKey}>Save key</Button>
        <label>
          <span class="text-caption">Chat model</span>
          <input type="text" value={groq.chat_model} onchange={(e) => saveGroq({ chat_model: e.currentTarget.value })} />
        </label>
        <label>
          <span class="text-caption">Vision model</span>
          <input type="text" value={groq.vision_model} onchange={(e) => saveGroq({ vision_model: e.currentTarget.value })} />
        </label>
        <label>
          <span class="text-caption">Whisper model</span>
          <input type="text" value={groq.whisper_model} onchange={(e) => saveGroq({ whisper_model: e.currentTarget.value })} />
        </label>
      </div>
      <div class="checks">
        <label><input type="checkbox" checked={groq.enable_night_summary} onchange={(e) => saveGroq({ enable_night_summary: e.currentTarget.checked })} /> Night review summary</label>
        <label><input type="checkbox" checked={groq.enable_voice_hotkey} onchange={(e) => saveGroq({ enable_voice_hotkey: e.currentTarget.checked })} /> Voice hotkey ({groq.voice_hotkey})</label>
        <label><input type="checkbox" checked={groq.enable_photo_parse} onchange={(e) => saveGroq({ enable_photo_parse: e.currentTarget.checked })} /> Photo meal suggestions</label>
      </div>
    </Card>
  {/if}

  {#if sync}
    <Card title="Data sources" subtitle="Catalog sync status">
      <p class="text-body">{sync.summary}</p>
      <p class="text-caption">State: {sync.sync_state} · {sync.catalog_food_count} catalog foods · full sync: {sync.full_sync_available ? 'yes' : 'no (bundled subset)'}</p>
    </Card>
  {/if}

  <Card title="Backup & export" subtitle="Rotating local copies + manual JSON/CSV">
    <p class="text-caption">Automatic backups run at most once per day (keeps last 7). Manual export does not include the full USDA/OFF catalog.</p>
    <div class="row">
      <Button disabled={busy} onclick={handleBackupNow}>Backup now</Button>
      <Button variant="secondary" onclick={handleExportJson}>Export JSON</Button>
      <Button variant="secondary" onclick={handleExportCsv}>Export diary CSV</Button>
    </div>
    <div class="row">
      <label class="file-btn"><input type="file" accept="application/json,.json" onchange={onImportJson} hidden /> Import JSON</label>
      <label class="file-btn"><input type="file" accept="text/csv,.csv" onchange={onImportCsv} hidden /> Import diary CSV</label>
    </div>
    {#if backups.length}
      <ul class="backup-list">
        {#each backups as b}
          <li>
            <span>{b.filename}</span>
            <button type="button" class="linkish" onclick={() => handleRestore(b.filename)}>Restore</button>
          </li>
        {/each}
      </ul>
    {:else}
      <p class="text-caption">No file backups yet.</p>
    {/if}
  </Card>

  {#if appInfo}
    <Card title="About Marrow" subtitle="Version and data location">
      <dl class="about">
        <div><dt>Version</dt><dd>{appInfo.version}</dd></div>
        <div><dt>Platform</dt><dd>{appInfo.platform}</dd></div>
        <div><dt>Schema</dt><dd>v{appInfo.schema_version}</dd></div>
        <div><dt>Data folder</dt><dd class="mono">{appInfo.data_dir}</dd></div>
      </dl>
    </Card>
  {/if}

  <Card title="Keyboard shortcuts" subtitle="Global">
    <ul class="shortcuts">
      <li><kbd>Ctrl</kbd> + <kbd>K</kbd> — Command palette (search, navigate, quick log)</li>
      <li><kbd>Ctrl</kbd> + <kbd>L</kbd> — Focus Today quick log</li>
      <li><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>V</kbd> — Voice note (when Groq key is set)</li>
    </ul>
  </Card>
</main>

<style>
  .settings {
    max-width: 720px;
    margin: 0 auto;
    padding: var(--space-6);
    display: flex;
    flex-direction: column;
    gap: var(--space-5);
  }

  .lede {
    color: var(--color-text-secondary);
    margin-top: calc(-1 * var(--space-2));
  }

  .banner {
    padding: var(--space-3) var(--space-4);
    border-radius: var(--radius-md);
  }

  .banner.error {
    background: rgba(255, 107, 107, 0.12);
    color: var(--color-danger);
  }

  .banner.ok {
    background: rgba(107, 207, 142, 0.12);
    color: var(--color-success);
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: var(--space-4);
  }

  label {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  label.full {
    grid-column: 1 / -1;
  }

  select,
  input[type='text'],
  input[type='password'] {
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-sm);
    border: 1px solid var(--color-border-subtle);
    background: var(--color-surface);
    color: var(--color-text);
  }

  .checks {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
    margin-top: var(--space-3);
  }

  .checks label {
    flex-direction: row;
    align-items: center;
    gap: var(--space-3);
  }

  .row {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-3);
    margin: var(--space-3) 0;
  }

  .file-btn {
    display: inline-flex;
    align-items: center;
    padding: var(--space-2) var(--space-4);
    border-radius: var(--radius-full);
    background: var(--color-surface);
    cursor: pointer;
  }

  .backup-list {
    list-style: none;
    padding: 0;
    margin: var(--space-3) 0 0;
  }

  .backup-list li {
    display: flex;
    justify-content: space-between;
    padding: var(--space-2) 0;
    border-bottom: 1px solid var(--color-border-subtle);
  }

  .linkish {
    color: var(--color-accent);
  }

  .shortcuts {
    margin: 0;
    padding-left: var(--space-5);
  }

  kbd {
    font-size: 0.85em;
    padding: 0.1em 0.35em;
    border-radius: 4px;
    border: 1px solid var(--color-border-subtle);
    background: var(--color-surface);
  }

  .about {
    display: grid;
    gap: var(--space-2);
    margin: 0;
  }

  .about div {
    display: grid;
    grid-template-columns: 7rem 1fr;
    gap: var(--space-2);
  }

  .about dt {
    color: var(--color-text-secondary);
    font-size: 0.9rem;
  }

  .about dd {
    margin: 0;
  }

  .mono {
    font-family: ui-monospace, monospace;
    font-size: 0.85rem;
    word-break: break-all;
  }
</style>
