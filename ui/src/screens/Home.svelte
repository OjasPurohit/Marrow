<script lang="ts">
  import { onMount } from 'svelte';
  import Button from '@/components/Button.svelte';
  import Card from '@/components/Card.svelte';
  import { getAppInfo, ping, type AppInfo } from '@/lib/bridge';

  let info: AppInfo | null = $state(null);
  let bridgeStatus = $state('…');

  onMount(async () => {
    bridgeStatus = await ping();
    info = await getAppInfo();
  });
</script>

<main class="home">
  <div class="hero">
    <p class="text-overline">Nutrition</p>
    <h1 class="text-display">Eat with intention.</h1>
    <p class="text-body lede">
      Marrow is your offline-first diet tracker — calm, precise, and built for the long game.
    </p>
    <div class="actions">
      <Button variant="primary" size="lg">Log a meal</Button>
      <Button variant="secondary" size="lg">Browse foods</Button>
    </div>
  </div>

  <div class="grid">
    <Card title="Bridge" subtitle="Python ↔ UI connection">
      <dl class="meta">
        <dt>Status</dt>
        <dd>{bridgeStatus}</dd>
        {#if info}
          <dt>Version</dt>
          <dd>{info.version}</dd>
          <dt>Schema</dt>
          <dd>v{info.schema_version}</dd>
          <dt>Data</dt>
          <dd class="mono">{info.data_dir}</dd>
        {/if}
      </dl>
    </Card>

    <Card title="Today" subtitle="M2 will wire real diary data">
      <div class="rings" aria-hidden="true">
        <svg viewBox="0 0 120 120" class="ring-chart">
          <circle cx="60" cy="60" r="48" class="ring-bg" />
          <circle cx="60" cy="60" r="48" class="ring-fg" stroke-dasharray="210 90" />
        </svg>
        <div class="ring-label">
          <span class="text-title-2">1,840</span>
          <span class="text-caption">kcal remaining</span>
        </div>
      </div>
    </Card>
  </div>
</main>

<style>
  .home {
    flex: 1;
    overflow: auto;
    padding: var(--space-8) var(--space-6) var(--space-12);
    max-width: 1100px;
    margin: 0 auto;
    width: 100%;
  }

  .hero {
    margin-bottom: var(--space-10);
  }

  .hero h1 {
    margin: var(--space-2) 0 var(--space-4);
    max-width: 14ch;
  }

  .lede {
    max-width: 42ch;
    color: var(--color-text-secondary);
    margin: 0 0 var(--space-6);
  }

  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-3);
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: var(--space-6);
  }

  .meta {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: var(--space-2) var(--space-4);
    margin: 0;
  }

  .meta dt {
    color: var(--color-text-tertiary);
    font-size: 0.8125rem;
  }

  .meta dd {
    margin: 0;
    font-size: 0.9375rem;
  }

  .mono {
    font-family: ui-monospace, monospace;
    font-size: 0.75rem;
    word-break: break-all;
  }

  .rings {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 160px;
  }

  .ring-chart {
    width: 140px;
    height: 140px;
    transform: rotate(-90deg);
  }

  .ring-bg {
    fill: none;
    stroke: var(--color-surface);
    stroke-width: 10;
  }

  .ring-fg {
    fill: none;
    stroke: var(--color-accent);
    stroke-width: 10;
    stroke-linecap: round;
    transition: stroke-dasharray var(--duration-normal) var(--ease-out-quart);
  }

  .ring-label {
    position: absolute;
    text-align: center;
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
  }
</style>
