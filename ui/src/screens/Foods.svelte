<script lang="ts">
  import { onMount } from 'svelte';
  import Card from '@/components/Card.svelte';
  import EmptyState from '@/components/EmptyState.svelte';
  import {
    ensureFoodBridge,
    searchFoods,
    type FoodSearchResult,
  } from '@/lib/foods';
  import { parseHashQuery } from '@/lib/routes';

  let query = $state('');
  let results = $state<FoodSearchResult[]>([]);
  let elapsedMs = $state<number | null>(null);
  let loading = $state(false);
  let bridgeReady = $state(false);
  let debounce: ReturnType<typeof setTimeout> | undefined;

  async function runSearch(q: string) {
    loading = true;
    try {
      const res = await searchFoods(q, 20);
      results = res.results;
      elapsedMs = res.elapsed_ms;
    } finally {
      loading = false;
    }
  }

  function onInput() {
    clearTimeout(debounce);
    debounce = setTimeout(() => runSearch(query), 120);
  }

  onMount(async () => {
    bridgeReady = await ensureFoodBridge();
    const q = parseHashQuery(location.hash).get('q');
    if (q) {
      query = q;
      await runSearch(q);
    } else {
      await runSearch('ban');
    }
  });
</script>

<main class="foods">
  <div class="foods-inner">
    <header class="hero">
      <h1 class="text-title">Foods</h1>
      <p class="text-body subtle">
        Search the offline catalog — fuzzy match as you type.
        {#if bridgeReady}
          <span class="pill">Bridge connected</span>
        {:else}
          <span class="pill muted">Browser demo</span>
        {/if}
      </p>
    </header>

    <Card>
      <label class="search-label" for="food-search">Search foods</label>
      <div class="search-row">
        <input
          id="food-search"
          type="search"
          placeholder="e.g. banana, rice, dal…"
          bind:value={query}
          oninput={onInput}
          autocomplete="off"
          spellcheck="false"
        />
        {#if loading}
          <span class="meta" aria-live="polite">Searching…</span>
        {:else if elapsedMs !== null}
          <span class="meta">{elapsedMs.toFixed(1)} ms</span>
        {/if}
      </div>

      {#if !loading && query.trim().length >= 2 && results.length === 0}
        <EmptyState
          title="No foods matched"
          detail="Try a shorter spelling, a generic name (rice, dal), or check Settings for catalog status."
        />
      {:else}
        <ul class="results" role="listbox" aria-label="Food results">
          {#each results as item (item.id)}
            <li role="option" aria-selected="false">
              <div class="row">
                <span class="name">{item.name}</span>
                <span class="tags">
                  <span class="tag">{item.source}</span>
                  {#if item.preparation !== 'unknown'}
                    <span class="tag">{item.preparation}</span>
                  {/if}
                </span>
              </div>
              {#if item.brand}
                <span class="brand">{item.brand}</span>
              {/if}
            </li>
          {:else}
            {#if query.trim().length < 2}
              <li class="hint text-caption">Type at least two characters to search the offline catalog.</li>
            {/if}
          {/each}
        </ul>
      {/if}
    </Card>
  </div>
</main>

<style>
  .foods {
    padding: var(--space-6);
    min-height: calc(100vh - 72px);
  }

  .foods-inner {
    max-width: 720px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: var(--space-6);
  }

  .hero h1 {
    margin: 0 0 var(--space-2);
  }

  .subtle {
    color: var(--color-text-secondary);
    margin: 0;
    display: flex;
    align-items: center;
    gap: var(--space-3);
    flex-wrap: wrap;
  }

  .pill {
    font-size: 0.75rem;
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-full);
    background: var(--color-accent-muted);
    color: var(--color-accent);
  }

  .pill.muted {
    background: var(--color-surface);
    color: var(--color-text-secondary);
  }

  .search-label {
    display: block;
    font-size: 0.875rem;
    font-weight: 500;
    margin-bottom: var(--space-2);
    color: var(--color-text-secondary);
  }

  .search-row {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    margin-bottom: var(--space-4);
  }

  input[type='search'] {
    flex: 1;
    padding: var(--space-3) var(--space-4);
    border-radius: var(--radius-lg);
    border: 1px solid var(--color-border-subtle);
    background: var(--color-bg-elevated);
    color: var(--color-text);
    font-size: 1rem;
    transition: border-color var(--duration-fast) var(--ease-out-quart),
      box-shadow var(--duration-fast) var(--ease-out-quart);
  }

  input[type='search']:focus {
    outline: none;
    border-color: var(--color-accent);
    box-shadow: 0 0 0 3px var(--color-accent-muted);
  }

  .meta {
    font-size: 0.8125rem;
    color: var(--color-text-tertiary);
    white-space: nowrap;
  }

  .results {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
  }

  .results li {
    padding: var(--space-3) var(--space-3);
    border-radius: var(--radius-md);
    transition: background var(--duration-fast) var(--ease-out-quart);
  }

  .results li[role='option']:hover {
    background: var(--color-surface-hover);
  }

  .hint {
    padding: var(--space-4);
    color: var(--color-text-secondary);
    text-align: center;
  }

  .row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: var(--space-3);
  }

  .name {
    font-weight: 500;
  }

  .tags {
    display: flex;
    gap: var(--space-1);
    flex-shrink: 0;
  }

  .tag {
    font-size: 0.6875rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    padding: 2px 6px;
    border-radius: var(--radius-sm);
    background: var(--color-surface);
    color: var(--color-text-secondary);
  }

  .brand {
    font-size: 0.8125rem;
    color: var(--color-text-tertiary);
  }

</style>
