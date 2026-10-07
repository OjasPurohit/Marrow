<script lang="ts">
  import type { Route } from '@/lib/routes';

  interface Props {
    route: Route;
    onNavigate?: (route: Route) => void;
  }

  let { route, onNavigate }: Props = $props();
  const dev = import.meta.env.DEV;
</script>

<header class="chrome">
  <div class="chrome-inner">
    <div class="brand">
      <span class="mark" aria-hidden="true"></span>
      <span class="text-headline">Marrow</span>
    </div>
    <nav class="nav" aria-label="Main">
      <button
        type="button"
        class:active={route === 'home'}
        onclick={() => onNavigate?.('home')}
      >
        Today
      </button>
      <button
        type="button"
        class:active={route === 'nightReview'}
        onclick={() => onNavigate?.('nightReview')}
      >
        Review
      </button>
      <button
        type="button"
        class:active={route === 'history'}
        onclick={() => onNavigate?.('history')}
      >
        History
      </button>
      <button
        type="button"
        class:active={route === 'trends'}
        onclick={() => onNavigate?.('trends')}
      >
        Trends
      </button>
      <button
        type="button"
        class:active={route === 'foods'}
        onclick={() => onNavigate?.('foods')}
      >
        Foods
      </button>
      <button
        type="button"
        class:active={route === 'profile'}
        onclick={() => onNavigate?.('profile')}
      >
        Profile
      </button>
      <button
        type="button"
        class:active={route === 'settings'}
        onclick={() => onNavigate?.('settings')}
      >
        Settings
      </button>
      {#if dev}
        <button
          type="button"
          class:active={route === 'gallery'}
          onclick={() => onNavigate?.('gallery')}
        >
          Lab
        </button>
      {/if}
    </nav>
  </div>
</header>

<style>
  .chrome {
    position: sticky;
    top: 0;
    z-index: 10;
    padding: var(--space-3) var(--space-6);
    background: var(--material-chrome);
    backdrop-filter: blur(var(--material-blur)) saturate(var(--material-saturate));
    border-bottom: 1px solid var(--color-border-subtle);
    box-shadow: var(--shadow-sm);
  }

  .chrome-inner {
    max-width: 1100px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-6);
  }

  .brand {
    display: flex;
    align-items: center;
    gap: var(--space-3);
  }

  .mark {
    width: 10px;
    height: 10px;
    border-radius: var(--radius-full);
    background: linear-gradient(135deg, var(--color-accent), #c97b5a);
    box-shadow: 0 0 12px var(--color-accent-muted);
  }

  .nav {
    display: flex;
    gap: var(--space-1);
    padding: var(--space-1);
    border-radius: var(--radius-full);
    background: var(--color-surface);
  }

  .nav button {
    padding: var(--space-2) var(--space-4);
    border-radius: var(--radius-full);
    font-size: 0.9375rem;
    font-weight: 500;
    color: var(--color-text-secondary);
    transition: background var(--duration-fast) var(--ease-out-quart),
      color var(--duration-fast) var(--ease-out-quart),
      transform var(--duration-instant) var(--ease-out-quart);
  }

  .nav button:active {
    transform: scale(0.97);
  }

  .nav button.active {
    background: var(--color-bg-elevated);
    color: var(--color-text);
    box-shadow: var(--shadow-sm);
  }

  .nav button:hover:not(.active) {
    color: var(--color-text);
    background: var(--color-surface-hover);
  }
</style>
