<script lang="ts">
  import { onMount } from 'svelte';
  import Card from '@/components/Card.svelte';
  import CalendarHeatmap from '@/components/CalendarHeatmap.svelte';
  import EmptyState from '@/components/EmptyState.svelte';
  import {
    getDiaryHistoryMonth,
    type DiaryHistoryPayload,
    type HistoryDay,
  } from '@/lib/history';
  import { formatKcal } from '@/lib/parseQuantity';

  const now = new Date();
  let year = $state(now.getFullYear());
  let month = $state(now.getMonth() + 1);
  let history = $state<DiaryHistoryPayload | null>(null);
  let error = $state<string | null>(null);
  let loading = $state(true);
  let selectedDate = $state<string | null>(null);

  const monthLabel = $derived(
    new Date(year, month - 1, 1).toLocaleString(undefined, { month: 'long', year: 'numeric' }),
  );

  const recentDays = $derived(
    (history?.days ?? [])
      .filter((d) => d.logged)
      .slice()
      .reverse()
      .slice(0, 14),
  );

  async function load() {
    loading = true;
    error = null;
    try {
      history = await getDiaryHistoryMonth(year, month);
    } catch (e) {
      error = e instanceof Error ? e.message : 'Could not load history';
    } finally {
      loading = false;
    }
  }

  function shiftMonth(delta: number) {
    let m = month + delta;
    let y = year;
    if (m < 1) {
      m = 12;
      y -= 1;
    } else if (m > 12) {
      m = 1;
      y += 1;
    }
    month = m;
    year = y;
    load();
  }

  function openDay(day: HistoryDay | string) {
    const iso = typeof day === 'string' ? day : day.log_date;
    selectedDate = iso;
    location.hash = `/night-review?date=${iso}`;
  }

  function balanceShort(day: HistoryDay): string {
    if (!day.logged) return 'No log';
    if (day.data_incomplete) return 'Incomplete data';
    if (day.energy_balance_status === 'DEFICIT') return 'Deficit';
    if (day.energy_balance_status === 'SURPLUS') return 'Surplus';
    if (day.energy_balance_status === 'ON_TARGET') return 'On target';
    return 'Logged';
  }

  onMount(() => {
    load();
  });
</script>

<main class="page">
  <header class="hero">
    <div>
      <p class="text-caption">History</p>
      <h1 class="text-title-1">Your log</h1>
    </div>
    {#if history}
      <div class="stats text-caption">
        <span>{history.days_logged} days logged</span>
        <span>Streak {history.streak.current}d</span>
      </div>
    {/if}
  </header>

  <Card title={monthLabel} subtitle="Tap a day for full breakdown">
    <div class="month-nav">
      <button type="button" class="nav-btn" onclick={() => shiftMonth(-1)} aria-label="Previous month">
        ←
      </button>
      <button type="button" class="nav-btn" onclick={() => shiftMonth(1)} aria-label="Next month">
        →
      </button>
    </div>
    {#if loading}
      <p class="text-caption">Loading calendar…</p>
    {:else if error}
      <p class="error">{error}</p>
    {:else if history}
      <CalendarHeatmap {year} {month} days={history.days} {selectedDate} onSelect={openDay} />
    {/if}
  </Card>

  <Card title="Recent days" subtitle="Newest logged days in this month">
    {#if recentDays.length === 0}
      <EmptyState
        title="No logged days this month"
        detail="Log meals on Today — days will show up here with balance colors on the calendar."
        actionLabel="Go to Today"
        onAction={() => { location.hash = '#/'; }}
      />
    {:else}
      <ul class="day-list">
        {#each recentDays as day}
          <li>
            <button type="button" class="day-row" onclick={() => openDay(day)}>
              <span class="date">{day.log_date}</span>
              <span class="meta">
                {formatKcal(day.energy_kcal)} · {balanceShort(day)}
                {#if day.data_incomplete}
                  <span class="badge">!</span>
                {/if}
              </span>
            </button>
          </li>
        {/each}
      </ul>
    {/if}
  </Card>
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

  .stats {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: var(--space-1);
    color: var(--color-text-secondary);
  }

  .month-nav {
    display: flex;
    justify-content: flex-end;
    gap: var(--space-2);
    margin-bottom: var(--space-3);
  }

  .nav-btn {
    width: 36px;
    height: 36px;
    border-radius: var(--radius-full);
    background: var(--color-surface);
    color: var(--color-text);
  }

  .day-list {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .day-row {
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--space-3) var(--space-4);
    border-radius: var(--radius-lg);
    background: var(--color-surface);
    text-align: left;
  }

  .day-row:hover {
    background: var(--color-surface-hover);
  }

  .date {
    font-weight: 600;
  }

  .meta {
    color: var(--color-text-secondary);
    font-size: 0.875rem;
  }

  .badge {
    display: inline-flex;
    margin-left: var(--space-1);
    color: var(--color-warning);
    font-weight: 700;
  }

  .error {
    color: var(--color-danger, #e57373);
  }
</style>
