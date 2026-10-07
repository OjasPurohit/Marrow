<script lang="ts">
  import { onMount } from 'svelte';
  import Card from '@/components/Card.svelte';
  import EmptyState from '@/components/EmptyState.svelte';
  import TrendLineSvg from '@/components/TrendLineSvg.svelte';
  import { getUserProfile, type UserProfile } from '@/lib/profile';
  import {
    addWeightEntry,
    deleteWeightEntry,
    getTrendSeries,
    getWeightLogWithTrend,
    type TrendRange,
    type TrendSeriesPayload,
    type WeightEntry,
  } from '@/lib/trends';

  const ranges: TrendRange[] = [7, 30, 90];
  let rangeDays = $state<TrendRange>(30);
  let trends = $state<TrendSeriesPayload | null>(null);
  let weightLog = $state<WeightEntry[]>([]);
  let profile = $state<UserProfile | null>(null);
  let selectedMicros = $state<string[]>(['fiber_g', 'iron_mg', 'vitamin_d_ug']);
  let loading = $state(true);
  let error = $state<string | null>(null);

  let weightInput = $state('');
  let weightDate = $state(new Date().toISOString().slice(0, 10));
  let weightNote = $state('');
  let savingWeight = $state(false);

  const microOptions = $derived(
    Object.keys(profile?.micronutrient_targets ?? {}).length
      ? Object.keys(profile!.micronutrient_targets!)
      : ['fiber_g', 'iron_mg', 'vitamin_d_ug', 'calcium_mg', 'vitamin_c_mg'],
  );

  async function refresh() {
    loading = true;
    error = null;
    try {
      trends = await getTrendSeries(rangeDays, selectedMicros);
      const weightPayload = await getWeightLogWithTrend(120);
      weightLog = weightPayload.entries;
    } catch (e) {
      error = e instanceof Error ? e.message : 'Could not load trends';
    } finally {
      loading = false;
    }
  }

  async function submitWeight() {
    const kg = parseFloat(weightInput);
    if (!Number.isFinite(kg) || kg <= 0) return;
    savingWeight = true;
    try {
      await addWeightEntry({
        weight_kg: kg,
        logged_date: weightDate,
        note: weightNote.trim() || undefined,
      });
      weightInput = '';
      weightNote = '';
      await refresh();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Could not save weight';
    } finally {
      savingWeight = false;
    }
  }

  async function removeWeight(id: number) {
    await deleteWeightEntry(id);
    await refresh();
  }

  function toggleMicro(key: string) {
    if (selectedMicros.includes(key)) {
      selectedMicros = selectedMicros.filter((k) => k !== key);
    } else if (selectedMicros.length < 4) {
      selectedMicros = [...selectedMicros, key];
    }
    refresh();
  }

  function microLabel(key: string): string {
    return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  }

  onMount(async () => {
    profile = await getUserProfile();
    await refresh();
  });
</script>

<main class="page">
  <header class="hero">
    <div>
      <p class="text-caption">Trends</p>
      <h1 class="text-title-1">Patterns</h1>
    </div>
    <div class="range" role="tablist" aria-label="Trend range">
      {#each ranges as r}
        <button
          type="button"
          role="tab"
          aria-selected={rangeDays === r}
          class:active={rangeDays === r}
          onclick={() => {
            rangeDays = r;
            refresh();
          }}
        >
          {r}d
        </button>
      {/each}
    </div>
  </header>

  {#if loading && !trends}
    <p class="text-caption">Loading trends…</p>
  {:else if error}
    <p class="error">{error}</p>
  {:else if trends}
    {#if trends.days_logged === 0}
      <EmptyState
        title="Not enough history yet"
        detail="Log a few days on Today — trends and rolling averages will appear here."
        actionLabel="Go to Today"
        onAction={() => { location.hash = '#/'; }}
      />
    {/if}
    <Card title="Intake" subtitle="Solid = daily · dashed = 7-day rolling average">
      <TrendLineSvg
        dates={trends.dates}
        values={trends.energy_kcal}
        secondary={trends.rolling_7_energy_kcal}
        label="Calories"
        unit="kcal"
        width={340}
      />
      <TrendLineSvg
        dates={trends.dates}
        values={trends.protein_g}
        label="Protein"
        unit="g"
        width={340}
        color="var(--color-success, #6bbf8a)"
      />
    </Card>

    <Card title="Energy balance" subtitle="Daily delta vs target and rolling 7-day average">
      <TrendLineSvg
        dates={trends.dates}
        values={trends.energy_delta_kcal}
        secondary={trends.rolling_7_balance_kcal}
        label="Balance"
        unit="kcal"
        width={340}
      />
      {#if trends.weekly_balance.length}
        <ul class="weekly">
          {#each trends.weekly_balance as week}
            <li>
              <span>Week of {week.week_start}</span>
              <span>
                avg {week.avg_energy_delta_kcal ?? '—'} kcal · cum {week.cumulative_balance_kcal ?? '—'}
              </span>
            </li>
          {/each}
        </ul>
      {/if}
    </Card>

    <Card title="Micronutrients" subtitle="Choose up to four tracked nutrients">
      <div class="chips">
        {#each microOptions.slice(0, 12) as key}
          <button
            type="button"
            class="chip"
            class:on={selectedMicros.includes(key)}
            onclick={() => toggleMicro(key)}
          >
            {microLabel(key)}
          </button>
        {/each}
      </div>
      {#each selectedMicros as key}
        {#if trends.micronutrients[key]}
          <TrendLineSvg
            dates={trends.dates}
            values={trends.micronutrients[key]}
            label={microLabel(key)}
            width={340}
          />
        {/if}
      {/each}
    </Card>

    <Card title="Weight" subtitle="Log body weight · dashed line = 7-day smoothed trend">
      <form class="weight-form" onsubmit={(e) => { e.preventDefault(); submitWeight(); }}>
        <label>
          <span class="text-caption">kg</span>
          <input type="number" step="0.1" min="1" bind:value={weightInput} required />
        </label>
        <label>
          <span class="text-caption">Date</span>
          <input type="date" bind:value={weightDate} required />
        </label>
        <label class="grow">
          <span class="text-caption">Note</span>
          <input type="text" bind:value={weightNote} placeholder="Optional" />
        </label>
        <button type="submit" class="save" disabled={savingWeight}>Add</button>
      </form>

      <TrendLineSvg
        dates={trends.dates}
        values={trends.weight_kg}
        secondary={trends.weight_smooth_kg}
        label="Weight"
        unit="kg"
        width={340}
      />

      <ul class="weight-list">
        {#each weightLog.slice(0, 8) as entry}
          <li>
            <span>{entry.logged_date} — {entry.weight_kg} kg</span>
            <button type="button" class="del" onclick={() => removeWeight(entry.id)}>Remove</button>
          </li>
        {/each}
      </ul>
    </Card>

    <p class="text-caption foot">{trends.days_logged} days logged in this window</p>
  {/if}
</main>

<style>
  .page {
    max-width: 720px;
    margin: 0 auto;
    padding: var(--space-6);
    display: flex;
    flex-direction: column;
    gap: var(--space-5);
  }

  .hero {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: var(--space-4);
  }

  .range {
    display: flex;
    gap: var(--space-1);
    padding: var(--space-1);
    border-radius: var(--radius-full);
    background: var(--color-surface);
  }

  .range button {
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-full);
    font-size: 0.875rem;
    color: var(--color-text-secondary);
  }

  .range button.active {
    background: var(--color-bg-elevated);
    color: var(--color-text);
    box-shadow: var(--shadow-sm);
  }

  .weekly {
    list-style: none;
    margin: var(--space-4) 0 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
    font-size: 0.875rem;
    color: var(--color-text-secondary);
  }

  .weekly li {
    display: flex;
    justify-content: space-between;
    gap: var(--space-3);
  }

  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2);
    margin-bottom: var(--space-4);
  }

  .chip {
    padding: var(--space-1) var(--space-3);
    border-radius: var(--radius-full);
    font-size: 0.8125rem;
    background: var(--color-surface);
    color: var(--color-text-secondary);
  }

  .chip.on {
    background: color-mix(in srgb, var(--color-accent) 25%, var(--color-surface));
    color: var(--color-text);
  }

  .weight-form {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-3);
    align-items: flex-end;
    margin-bottom: var(--space-4);
  }

  .weight-form label {
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
  }

  .weight-form .grow {
    flex: 1;
    min-width: 120px;
  }

  input {
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-md);
    border: 1px solid var(--color-border-subtle);
    background: var(--color-bg-elevated);
    color: var(--color-text);
  }

  .save {
    padding: var(--space-2) var(--space-4);
    border-radius: var(--radius-full);
    background: var(--color-accent);
    color: var(--color-on-accent, #fff);
    font-weight: 600;
  }

  .weight-list {
    list-style: none;
    margin: var(--space-4) 0 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
    font-size: 0.875rem;
  }

  .weight-list li {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .del {
    color: var(--color-text-secondary);
    font-size: 0.8125rem;
  }

  .foot {
    text-align: center;
  }

  .error {
    color: var(--color-danger, #e57373);
  }
</style>
