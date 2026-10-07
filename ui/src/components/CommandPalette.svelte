<script lang="ts">
  import { searchFoods } from '@/lib/foods';
  import type { Route } from '@/lib/routes';
  import { routeHref } from '@/lib/routes';

  interface Props {
    open: boolean;
    onClose: () => void;
    onNavigate: (route: Route) => void;
    onQuickLog: () => void;
  }

  let { open, onClose, onNavigate, onQuickLog }: Props = $props();

  let query = $state('');
  let foodHits = $state<{ id: number; name: string }[]>([]);
  let searching = $state(false);

  const navItems: { id: string; label: string; route: Route; keywords: string }[] = [
    { id: 'nav-home', label: 'Go to Today', route: 'home', keywords: 'today log diary' },
    { id: 'nav-review', label: 'Go to Night review', route: 'nightReview', keywords: 'review micros' },
    { id: 'nav-history', label: 'Go to History', route: 'history', keywords: 'calendar streak' },
    { id: 'nav-trends', label: 'Go to Trends', route: 'trends', keywords: 'charts weight' },
    { id: 'nav-foods', label: 'Go to Foods', route: 'foods', keywords: 'search catalog' },
    { id: 'nav-profile', label: 'Go to Profile', route: 'profile', keywords: 'targets plan' },
    { id: 'nav-settings', label: 'Go to Settings', route: 'settings', keywords: 'preferences backup groq' },
  ];

  const actions = [
    { id: 'act-log', label: 'Quick log on Today', run: () => onQuickLog() },
    {
      id: 'act-settings',
      label: 'Open Settings',
      run: () => onNavigate('settings'),
    },
  ];

  const filteredNav = $derived(
    navItems.filter((item) => {
      const q = query.trim().toLowerCase();
      if (!q) return true;
      return item.label.toLowerCase().includes(q) || item.keywords.includes(q);
    }),
  );

  const filteredActions = $derived(
    actions.filter((item) => {
      const q = query.trim().toLowerCase();
      if (!q) return true;
      return item.label.toLowerCase().includes(q);
    }),
  );

  async function runSearch() {
    const q = query.trim();
    if (q.length < 2) {
      foodHits = [];
      return;
    }
    searching = true;
    try {
      const res = await searchFoods(q, 8);
      foodHits = res.results.map((r) => ({ id: r.id, name: r.name }));
    } finally {
      searching = false;
    }
  }

  $effect(() => {
    if (open) {
      query = '';
      foodHits = [];
      void runSearch();
    }
  });

  $effect(() => {
    if (!open) return;
    const q = query;
    const handle = setTimeout(() => void runSearch(), 180);
    return () => clearTimeout(handle);
  });

  function pickNav(route: Route) {
    onNavigate(route);
    onClose();
  }

  function pickFood(name: string) {
    location.hash = `/foods?q=${encodeURIComponent(name)}`;
    onClose();
  }

  function onKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      event.preventDefault();
      onClose();
    }
  }

</script>

{#if open}
  <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
  <div class="backdrop" role="presentation" onclick={onClose}></div>
  <div class="palette" role="dialog" aria-modal="true" aria-label="Command palette" tabindex="-1" onkeydown={onKeydown}>
    <input
      class="search"
      type="search"
      placeholder="Search food, jump to screen, or quick log…"
      bind:value={query}
      autofocus
    />
    <div class="sections">
      <section>
        <p class="text-overline">Navigate</p>
        <ul>
          {#each filteredNav as item}
            <li>
              <button type="button" onclick={() => pickNav(item.route)}>{item.label}</button>
            </li>
          {/each}
        </ul>
      </section>
      <section>
        <p class="text-overline">Actions</p>
        <ul>
          {#each filteredActions as item}
            <li>
              <button type="button" onclick={() => { item.run(); onClose(); }}>{item.label}</button>
            </li>
          {/each}
        </ul>
      </section>
      {#if foodHits.length}
        <section>
          <p class="text-overline">Foods {searching ? '…' : ''}</p>
          <ul>
            {#each foodHits as food}
              <li>
                <button type="button" onclick={() => pickFood(food.name)}>{food.name}</button>
              </li>
            {/each}
          </ul>
        </section>
      {/if}
    </div>
    <p class="hint text-caption">Ctrl+K · Esc to close · Foods open in {routeHref('foods')}</p>
  </div>
{/if}

<style>
  .backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.45);
    z-index: 40;
    animation: fade-in var(--duration-fast) var(--ease-out-quart);
  }

  .palette {
    position: fixed;
    top: 12vh;
    left: 50%;
    transform: translateX(-50%);
    animation: palette-in var(--duration-normal) var(--ease-out-quart);
    width: min(560px, calc(100vw - 2rem));
    z-index: 50;
    background: var(--color-bg-elevated);
    border: 1px solid var(--color-border-subtle);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-lg);
    padding: var(--space-4);
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  .search {
    width: 100%;
    padding: var(--space-3) var(--space-4);
    border-radius: var(--radius-md);
    border: 1px solid var(--color-border-subtle);
    background: var(--color-surface);
    color: var(--color-text);
    font-size: 1rem;
  }

  .sections {
    max-height: 50vh;
    overflow: auto;
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
  }

  section ul {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  section li button {
    width: 100%;
    text-align: left;
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-sm);
  }

  section li button:hover {
    background: var(--color-surface-hover);
  }

  .hint {
    color: var(--color-text-tertiary);
    margin: 0;
  }

  @keyframes fade-in {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  @keyframes palette-in {
    from {
      opacity: 0;
      transform: translateX(-50%) translateY(-8px);
    }
    to {
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .backdrop,
    .palette {
      animation: none;
    }
  }

</style>

<style>
  :global(html[data-reduced-motion='true']) .backdrop,
  :global(html[data-reduced-motion='true']) .palette {
    animation: none !important;
  }
</style>
