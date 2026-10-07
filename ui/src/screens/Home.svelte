<script lang="ts">
  import { onMount } from 'svelte';
  import Button from '@/components/Button.svelte';
  import Card from '@/components/Card.svelte';
  import MacroBar from '@/components/MacroBar.svelte';
  import NutrientRing from '@/components/NutrientRing.svelte';
  import {
    confirmAndSaveLog,
    ensureDiaryBridge,
    listDiaryEntriesForDate,
    parseFoodText,
    searchFoodsForSwap,
    swapDraftFood,
    type DiaryDayResponse,
    type ParseDraftItem,
  } from '@/lib/diary';
  import { confidenceLabel, formatAmount, formatGrams, formatKcal } from '@/lib/parseQuantity';
  import type { FoodSearchResult } from '@/lib/foods';

  let logText = $state('');
  let mealTag = $state('lunch');
  let parsing = $state(false);
  let saving = $state(false);
  let error = $state<string | null>(null);
  let drafts: ParseDraftItem[] = $state([]);
  let showConfirm = $state(false);
  let day: DiaryDayResponse | null = $state(null);
  let swapDraftId: string | null = $state(null);
  let swapQuery = $state('');
  let swapResults: FoodSearchResult[] = $state([]);

  const mealOptions = [
    'breakfast',
    'lunch',
    'dinner',
    'snack',
    'pre_workout',
    'post_workout',
  ];

  const mealLabels: Record<string, string> = {
    breakfast: 'Breakfast',
    lunch: 'Lunch',
    dinner: 'Dinner',
    snack: 'Snack',
    pre_workout: 'Pre-workout',
    post_workout: 'Post-workout',
    other: 'Other',
  };

  async function refreshToday() {
    day = await listDiaryEntriesForDate();
  }

  onMount(async () => {
    await ensureDiaryBridge();
    await refreshToday();
  });

  async function handleParse() {
    error = null;
    parsing = true;
    try {
      const result = await parseFoodText(logText.trim(), mealTag);
      drafts = result.items.map((item) => ({ ...item }));
      showConfirm = drafts.length > 0;
      if (!drafts.length) {
        error = 'Could not parse any items — try a quantity and food name.';
      }
    } catch (e) {
      error = e instanceof Error ? e.message : 'Parse failed';
    } finally {
      parsing = false;
    }
  }

  function removeDraft(id: string) {
    drafts = drafts.filter((d) => d.draft_id !== id);
    if (!drafts.length) showConfirm = false;
  }

  function updateDraftAmount(id: string, value: string) {
    const num = parseFloat(value);
    if (!Number.isFinite(num) || num <= 0) return;
    drafts = drafts.map((d) => (d.draft_id === id ? { ...d, amount: num } : d));
  }

  async function openSwap(id: string) {
    swapDraftId = id;
    swapQuery = '';
    swapResults = [];
  }

  async function runSwapSearch() {
    const res = await searchFoodsForSwap(swapQuery);
    swapResults = res.results;
  }

  async function pickSwap(food: FoodSearchResult) {
    if (!swapDraftId) return;
    const draft = drafts.find((d) => d.draft_id === swapDraftId);
    if (!draft) return;
    const updated = await swapDraftFood(draft, food);
    drafts = drafts.map((d) => (d.draft_id === swapDraftId ? updated : d));
    swapDraftId = null;
  }

  async function handleSave() {
    error = null;
    const items = drafts.filter((d) => d.food_id != null);
    if (!items.length) {
      error = 'Add at least one matched food before saving.';
      return;
    }
    saving = true;
    try {
      await confirmAndSaveLog({
        meal_tag: mealTag,
        source_text: logText.trim(),
        items: items.map((d) => ({
          food_id: d.food_id as number,
          amount: d.amount,
          unit: d.unit,
          match_confidence: d.match_confidence,
          raw_fragment: d.raw_fragment,
        })),
      });
      showConfirm = false;
      drafts = [];
      logText = '';
      await refreshToday();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Save failed';
    } finally {
      saving = false;
    }
  }

  function mealLabel(tag: string): string {
    return mealLabels[tag] ?? tag.replace(/_/g, ' ');
  }

  function formatLoggedAt(iso: string): string {
    const d = new Date(iso.replace(' ', 'T'));
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });
  }

  const totals = $derived(day?.totals);
  const targets = $derived(totals?.targets ?? {});
  const remaining = $derived(totals?.remaining);
  const balance = $derived(totals?.energy_balance);

  function balanceLabel(status: string | null | undefined): string {
    if (!status) return '—';
    if (status === 'ON_TARGET') return 'On target';
    if (status === 'DEFICIT') return 'Deficit';
    return 'Surplus';
  }
</script>

<main class="home">
  <div class="hero">
    <p class="text-overline">Today</p>
    <h1 class="text-display">Eat with intention.</h1>
    <p class="text-body lede">
      Type what you ate — quantities, roti, katori, Hinglish works. Review before it hits your diary.
    </p>
  </div>

  <Card title="Quick log" subtitle="Parse → confirm → save">
    <div class="log-form">
      <label class="field">
        <span class="text-caption">Meal</span>
        <select bind:value={mealTag}>
          {#each mealOptions as tag}
            <option value={tag}>{mealLabel(tag)}</option>
          {/each}
        </select>
      </label>
      <label class="field grow">
        <span class="text-caption">What did you eat?</span>
        <input
          type="text"
          placeholder="e.g. 2 roti, 1 katori dal, 1 medium banana"
          bind:value={logText}
          onkeydown={(e) => e.key === 'Enter' && handleParse()}
        />
      </label>
      <Button variant="primary" disabled={parsing || !logText.trim()} onclick={handleParse}>
        {parsing ? 'Parsing…' : 'Parse'}
      </Button>
    </div>
    {#if error}
      <p class="error text-caption">{error}</p>
    {/if}
  </Card>

  {#if showConfirm}
    <section class="confirm">
      <h2 class="text-title-2">Confirm items</h2>
      <ul class="draft-list">
        {#each drafts as item (item.draft_id)}
          <li class="draft">
            <div class="draft-main">
              <div>
                <span class="food-name">{item.food_name ?? 'No match'}</span>
                <span class="badge">{confidenceLabel(item.match_confidence)}</span>
              </div>
              <div class="meta text-caption">
                <label>
                  Qty
                  <input
                    type="number"
                    min="0.25"
                    step="0.25"
                    value={item.amount}
                    onchange={(e) => updateDraftAmount(item.draft_id, e.currentTarget.value)}
                  />
                </label>
                <span>{item.unit}</span>
                <span>{formatKcal(item.energy_kcal)} kcal</span>
              </div>
              {#if item.warnings?.length}
                <p class="warn text-caption">{item.warnings.join(', ')}</p>
              {/if}
            </div>
            <div class="draft-actions">
              <Button variant="secondary" size="sm" onclick={() => openSwap(item.draft_id)}>Swap</Button>
              <Button variant="secondary" size="sm" onclick={() => removeDraft(item.draft_id)}>Remove</Button>
            </div>
          </li>
        {/each}
      </ul>
      <div class="confirm-actions">
        <Button variant="secondary" onclick={() => (showConfirm = false)}>Cancel</Button>
        <Button variant="primary" disabled={saving} onclick={handleSave}>
          {saving ? 'Saving…' : 'Save to diary'}
        </Button>
      </div>
    </section>
  {/if}

  {#if swapDraftId}
    <Card title="Swap match" subtitle="Search catalog">
      <div class="swap-form">
        <input type="search" placeholder="Search foods" bind:value={swapQuery} oninput={runSwapSearch} />
      </div>
      <ul class="swap-results">
        {#each swapResults as food (food.id)}
          <li>
            <button type="button" onclick={() => pickSwap(food)}>{food.name}</button>
          </li>
        {/each}
      </ul>
      <Button variant="secondary" size="sm" onclick={() => (swapDraftId = null)}>Close</Button>
    </Card>
  {/if}

  {#if totals}
    <section class="summary">
      <div class="summary-head">
        <h2 class="text-title-2">Running totals</h2>
        {#if balance?.status}
          <p class="text-caption budget-note status-{balance.status}">
            {balanceLabel(balance.status)}
            {#if balance.energy_delta_kcal != null}
              · {balance.energy_delta_kcal > 0 ? '+' : ''}{Math.round(balance.energy_delta_kcal)} kcal vs target
            {/if}
            {#if balance.target_day_kind && balance.target_day_kind !== 'default'}
              · {balance.target_day_kind} day
            {/if}
          </p>
        {:else}
          <p class="text-caption budget-note">Log food to see deficit / surplus vs your targets.</p>
        {/if}
      </div>
      <div class="rings-row">
        <NutrientRing
          label="kcal"
          value={totals.energy_kcal}
          target={targets.energy_kcal ?? 2200}
          accent="var(--color-accent)"
        />
        <NutrientRing
          label="protein"
          value={totals.protein_g}
          target={targets.protein_g ?? 150}
          accent="var(--color-success)"
        />
        <NutrientRing
          label="carbs"
          value={totals.carbs_g}
          target={targets.carbs_g ?? 220}
          accent="var(--color-warning)"
        />
        <NutrientRing
          label="fat"
          value={totals.fat_g}
          target={targets.fat_g ?? 70}
          accent="#8ab4f8"
        />
        <NutrientRing
          label="left kcal"
          value={remaining?.energy_kcal}
          target={targets.energy_kcal ?? 2200}
          accent="var(--color-text-secondary)"
          size={72}
        />
      </div>
      <div class="bars">
        <MacroBar
          label="Calories"
          value={totals.energy_kcal}
          target={targets.energy_kcal ?? 2200}
          remaining={remaining?.energy_kcal ?? null}
          unit=" kcal"
          accent="var(--color-accent)"
        />
        <MacroBar
          label="Protein"
          value={totals.protein_g}
          target={targets.protein_g ?? 150}
          remaining={remaining?.protein_g ?? null}
          unit="g"
          accent="var(--color-success)"
        />
        <MacroBar
          label="Carbs"
          value={totals.carbs_g}
          target={targets.carbs_g ?? 220}
          remaining={remaining?.carbs_g ?? null}
          unit="g"
          accent="var(--color-warning)"
        />
        <MacroBar
          label="Fat"
          value={totals.fat_g}
          target={targets.fat_g ?? 70}
          remaining={remaining?.fat_g ?? null}
          unit="g"
          accent="#8ab4f8"
        />
      </div>
    </section>
  {/if}

  <section class="meals">
    <h2 class="text-title-2">Meals so far</h2>
    {#if day?.meals?.length}
      {#each day.meals as section (section.meal_tag)}
        <article class="meal-section">
          <header>
            <h3 class="text-title-3">{mealLabel(section.meal_tag)}</h3>
            <span class="meal-total text-caption">
              {formatKcal(section.totals.energy_kcal)} kcal · {formatGrams(section.totals.protein_g)} protein
            </span>
          </header>
          <ul class="meal-items">
            {#each section.entries as entry (entry.entry_id)}
              <li>
                <span>{formatAmount(entry.amount)} {entry.unit} {entry.food_name}</span>
                <span class="kcal">{formatKcal(entry.energy_kcal)} kcal</span>
              </li>
            {/each}
          </ul>
        </article>
      {/each}
    {:else}
      <p class="text-caption empty">Nothing logged yet today.</p>
    {/if}
  </section>

  <section class="timeline">
    <h2 class="text-title-2">Timeline</h2>
    {#if day?.entries?.length}
      <ol class="timeline-list">
        {#each day.entries as entry (entry.entry_id)}
          <li>
            <time class="text-caption">{formatLoggedAt(entry.logged_at)}</time>
            <div class="timeline-body">
              <span class="meal-pill">{mealLabel(entry.meal_tag)}</span>
              <span>{formatAmount(entry.amount)} {entry.unit} {entry.food_name}</span>
              <span class="kcal">{formatKcal(entry.energy_kcal)} kcal</span>
            </div>
          </li>
        {/each}
      </ol>
    {:else}
      <p class="text-caption empty">Your day’s log will appear here in order.</p>
    {/if}
  </section>
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
    margin-bottom: var(--space-8);
  }

  .hero h1 {
    margin: var(--space-2) 0 var(--space-4);
    max-width: 16ch;
  }

  .lede {
    max-width: 48ch;
    color: var(--color-text-secondary);
    margin: 0;
  }

  .log-form {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-3);
    align-items: flex-end;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
  }

  .field.grow {
    flex: 1;
    min-width: 200px;
  }

  input,
  select {
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-md);
    border: 1px solid var(--color-border-subtle);
    background: var(--color-bg-elevated);
    font: inherit;
  }

  .error {
    color: var(--color-danger, #c44);
    margin: var(--space-3) 0 0;
  }

  .confirm {
    margin: var(--space-8) 0;
  }

  .draft-list {
    list-style: none;
    padding: 0;
    margin: var(--space-4) 0;
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  .draft {
    display: flex;
    justify-content: space-between;
    gap: var(--space-4);
    padding: var(--space-4);
    border-radius: var(--radius-lg);
    background: var(--color-surface);
    border: 1px solid var(--color-border-subtle);
  }

  .food-name {
    font-weight: 600;
  }

  .badge {
    margin-left: var(--space-2);
    font-size: 0.75rem;
    padding: 0.1rem 0.5rem;
    border-radius: var(--radius-full);
    background: var(--color-accent-muted);
  }

  .meta {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-3);
    margin-top: var(--space-2);
    color: var(--color-text-secondary);
  }

  .meta input {
    width: 4rem;
    margin-left: var(--space-1);
  }

  .warn {
    color: var(--color-text-tertiary);
    margin: var(--space-2) 0 0;
  }

  .draft-actions {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .confirm-actions {
    display: flex;
    gap: var(--space-3);
    justify-content: flex-end;
  }

  .swap-form input {
    width: 100%;
  }

  .swap-results {
    list-style: none;
    padding: 0;
    margin: var(--space-3) 0;
  }

  .swap-results button {
    width: 100%;
    text-align: left;
    padding: var(--space-2);
    border-radius: var(--radius-md);
  }

  .swap-results button:hover {
    background: var(--color-surface-hover);
  }

  .summary {
    margin-top: var(--space-8);
    padding: var(--space-6);
    border-radius: var(--radius-xl);
    background: var(--color-bg-grouped);
    border: 1px solid var(--color-border-subtle);
  }

  .summary-head {
    margin-bottom: var(--space-5);
  }

  .budget-note {
    margin: var(--space-1) 0 0;
    color: var(--color-text-tertiary);
  }

  .status-DEFICIT {
    color: var(--color-warning);
  }

  .status-SURPLUS {
    color: var(--color-accent);
  }

  .status-ON_TARGET {
    color: var(--color-success);
  }

  .rings-row {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-4);
    justify-content: center;
    margin-bottom: var(--space-6);
  }

  .bars {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
  }

  .meals,
  .timeline {
    margin-top: var(--space-10);
  }

  .meal-section {
    margin-top: var(--space-5);
    padding: var(--space-4);
    border-radius: var(--radius-lg);
    background: var(--color-surface);
    border: 1px solid var(--color-border-subtle);
  }

  .meal-section header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: var(--space-3);
    margin-bottom: var(--space-3);
  }

  .meal-section h3 {
    margin: 0;
  }

  .meal-total {
    color: var(--color-text-secondary);
  }

  .meal-items {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .meal-items li {
    display: flex;
    justify-content: space-between;
    font-size: 0.9375rem;
  }

  .timeline-list {
    list-style: none;
    padding: 0;
    margin: var(--space-4) 0 0;
    border-left: 2px solid var(--color-border-subtle);
  }

  .timeline-list li {
    position: relative;
    padding: 0 0 var(--space-4) var(--space-5);
  }

  .timeline-list li::before {
    content: '';
    position: absolute;
    left: -5px;
    top: 0.35rem;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--color-accent);
  }

  .timeline-body {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-2);
    margin-top: var(--space-1);
  }

  .meal-pill {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    padding: 0.1rem 0.45rem;
    border-radius: var(--radius-full);
    background: var(--color-accent-muted);
    color: var(--color-text-secondary);
  }

  .kcal {
    color: var(--color-text-secondary);
  }

  .empty {
    margin: var(--space-4) 0 0;
    color: var(--color-text-tertiary);
  }
</style>
