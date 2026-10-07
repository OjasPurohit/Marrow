<script lang="ts">
  import Button from '@/components/Button.svelte';
  import Card from '@/components/Card.svelte';
  import { quickStartTracking } from '@/lib/profile';

  interface Props {
    onComplete: () => void;
  }

  let { onComplete }: Props = $props();

  let error = $state<string | null>(null);
  let loading = $state(false);

  async function start() {
    error = null;
    loading = true;
    try {
      await quickStartTracking();
      onComplete();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Could not start';
    } finally {
      loading = false;
    }
  }
</script>

<div class="onboarding">
  <Card title="Welcome to Marrow" subtitle="Log meals, see your day add up">
    <p class="text-body lede">
      After each meal, type what you ate in plain language — roti, katori, grams, Hinglish all work.
      Marrow matches foods, you confirm once, and today’s macros and micros update automatically.
    </p>
    <ul class="bullets text-caption">
      <li>Running totals for calories, protein, carbs, and fat on Today</li>
      <li>Full micronutrient picture on Night review</li>
      <li>After you log every day for a week, your <strong>weekly average</strong> appears on Today</li>
    </ul>
    <p class="text-caption note">
      Optional profile targets live under Profile later — no long setup required to start logging.
    </p>
    <div class="actions">
      <Button onclick={start} disabled={loading}>{loading ? 'Starting…' : 'Start logging'}</Button>
    </div>
    {#if error}
      <p class="error text-caption">{error}</p>
    {/if}
  </Card>
</div>

<style>
  .onboarding {
    position: fixed;
    inset: 0;
    z-index: 100;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: var(--space-6);
    background: color-mix(in srgb, var(--color-bg) 92%, transparent);
    backdrop-filter: blur(8px);
  }

  .lede {
    margin: 0 0 var(--space-4);
    max-width: 52ch;
    color: var(--color-text-secondary);
  }

  .bullets {
    margin: 0 0 var(--space-4);
    padding-left: 1.25rem;
    color: var(--color-text-secondary);
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .note {
    margin: 0 0 var(--space-4);
    opacity: 0.85;
  }

  .actions {
    display: flex;
    gap: var(--space-3);
  }

  .error {
    color: var(--color-danger);
    margin-top: var(--space-3);
  }
</style>
