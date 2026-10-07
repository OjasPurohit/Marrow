<script lang="ts">
  import { onMount } from 'svelte';
  import Button from '@/components/Button.svelte';
  import Card from '@/components/Card.svelte';
  import { getAppInfo, ping, type AppInfo } from '@/lib/bridge';
  import {
    confirmAndSaveLog,
    ensureDiaryBridge,
    listDiaryEntriesForDate,
    parseFoodText,
    searchFoodsForSwap,
    swapDraftFood,
    type DiaryEntry,
    type ParseDraftItem,
  } from '@/lib/diary';
  import { confidenceLabel, formatAmount, formatKcal } from '@/lib/parseQuantity';
  import type { FoodSearchResult } from '@/lib/foods';

  let info: AppInfo | null = $state(null);
  let bridgeStatus = $state('…');
  let logText = $state('');
  let mealTag = $state('lunch');
  let parsing = $state(false);
  let saving = $state(false);
  let error = $state<string | null>(null);
  let drafts: ParseDraftItem[] = $state([]);
  let showConfirm = $state(false);
  let todayEntries: DiaryEntry[] = $state([]);
  let todayKcal: number | null = $state(null);
  let swapDraftId: string | null = $state(null);
  let swapQuery = $state('');
  let swapResults: FoodSearchResult[] = $state([]);

  const mealOptions = ['breakfast', 'lunch', 'dinner', 'snack'];

  async function refreshToday() {
    const day = await listDiaryEntriesForDate();
    todayEntries = day.entries;
    todayKcal = day.totals.energy_kcal;
  }

  onMount(async () => {
    bridgeStatus = await ping();
    info = await getAppInfo();
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
            <option value={tag}>{tag}</option>
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

  <div class="grid">
    <Card title="Bridge" subtitle="Python ↔ UI connection">
      <dl class="meta-dl">
        <dt>Status</dt>
        <dd>{bridgeStatus}</dd>
        {#if info}
          <dt>Version</dt>
          <dd>{info.version}</dd>
          <dt>Schema</dt>
          <dd>v{info.schema_version}</dd>
        {/if}
      </dl>
    </Card>

    <Card title="Today's log" subtitle="Confirmed entries">
      <div class="rings">
        <div class="ring-label">
          <span class="text-title-2">{formatKcal(todayKcal)}</span>
          <span class="text-caption">kcal logged</span>
        </div>
      </div>
      {#if todayEntries.length}
        <ul class="today-list">
          {#each todayEntries as entry (entry.entry_id)}
            <li>
              <span>{formatAmount(entry.amount)} {entry.unit} {entry.food_name}</span>
              <span class="kcal">{formatKcal(entry.energy_kcal)} kcal</span>
            </li>
          {/each}
        </ul>
      {:else}
        <p class="text-caption empty">Nothing logged yet today.</p>
      {/if}
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

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: var(--space-6);
    margin-top: var(--space-8);
  }

  .meta-dl {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: var(--space-2) var(--space-4);
    margin: 0;
  }

  .meta-dl dt {
    color: var(--color-text-tertiary);
    font-size: 0.8125rem;
  }

  .meta-dl dd {
    margin: 0;
  }

  .rings {
    display: flex;
    justify-content: center;
    min-height: 80px;
    align-items: center;
  }

  .ring-label {
    text-align: center;
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
  }

  .today-list {
    list-style: none;
    padding: 0;
    margin: var(--space-4) 0 0;
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .today-list li {
    display: flex;
    justify-content: space-between;
    font-size: 0.9375rem;
  }

  .kcal {
    color: var(--color-text-secondary);
  }

  .empty {
    margin: var(--space-4) 0 0;
    color: var(--color-text-tertiary);
  }
</style>
