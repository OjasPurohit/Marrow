<script lang="ts">
  import type { HistoryDay } from '@/lib/history';

  type Props = {
    year: number;
    month: number;
    days: HistoryDay[];
    selectedDate?: string | null;
    onSelect?: (logDate: string) => void;
  };

  let { year, month, days, selectedDate = null, onSelect }: Props = $props();

  const weekdayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  const dayMap = $derived(new Map(days.map((d) => [d.log_date, d])));

  const cells = $derived.by(() => {
    const first = new Date(year, month - 1, 1);
    const last = new Date(year, month, 0);
    const startPad = (first.getDay() + 6) % 7;
    const out: { key: string; label: string; day?: HistoryDay }[] = [];
    for (let i = 0; i < startPad; i++) {
      out.push({ key: `pad-${i}`, label: '' });
    }
    for (let d = 1; d <= last.getDate(); d++) {
      const iso = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
      out.push({ key: iso, label: String(d), day: dayMap.get(iso) });
    }
    return out;
  });

  function heatClass(day: HistoryDay | undefined): string {
    if (!day?.logged) return 'empty';
    if (day.data_incomplete) return 'incomplete';
    const status = day.energy_balance_status;
    if (status === 'DEFICIT') return 'deficit';
    if (status === 'SURPLUS') return 'surplus';
    if (status === 'ON_TARGET') return 'target';
    return 'logged';
  }

  function handleKey(e: KeyboardEvent, iso: string) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onSelect?.(iso);
    }
  }
</script>

<div class="heatmap" role="grid" aria-label="Calendar heatmap">
  <div class="weekdays" role="row">
    {#each weekdayLabels as label}
      <span class="weekday" role="columnheader">{label}</span>
    {/each}
  </div>
  <div class="grid" role="rowgroup">
    {#each cells as cell}
      {#if cell.day || cell.label}
        <button
          type="button"
          class="cell {heatClass(cell.day)}"
          class:selected={cell.key === selectedDate}
          disabled={!cell.day}
          role="gridcell"
          aria-label={cell.key}
          onclick={() => cell.day && onSelect?.(cell.key)}
          onkeydown={(e) => cell.day && handleKey(e, cell.key)}
        >
          <span>{cell.label}</span>
          {#if cell.day?.data_incomplete}
            <span class="dot" aria-hidden="true"></span>
          {/if}
        </button>
      {:else}
        <span class="cell pad" aria-hidden="true"></span>
      {/if}
    {/each}
  </div>
</div>

<style>
  .heatmap {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .weekdays,
  .grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: var(--space-1);
  }

  .weekday {
    text-align: center;
    font-size: 0.6875rem;
    color: var(--color-text-secondary);
  }

  .cell {
    position: relative;
    aspect-ratio: 1;
    border-radius: var(--radius-md);
    font-size: 0.8125rem;
    font-weight: 500;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid transparent;
    transition: transform var(--duration-fast) var(--ease-out-quart);
  }

  .cell:not(:disabled):hover {
    transform: scale(1.04);
  }

  .cell:focus-visible {
    outline: 2px solid var(--color-accent);
    outline-offset: 2px;
  }

  .cell.pad {
    visibility: hidden;
  }

  .cell.empty {
    background: var(--color-surface);
    color: var(--color-text-secondary);
  }

  .cell.logged {
    background: color-mix(in srgb, var(--color-accent) 35%, var(--color-surface));
  }

  .cell.target {
    background: color-mix(in srgb, var(--color-success, #6bbf8a) 40%, var(--color-surface));
  }

  .cell.deficit {
    background: color-mix(in srgb, var(--color-warning) 35%, var(--color-surface));
  }

  .cell.surplus {
    background: color-mix(in srgb, var(--color-danger, #e57373) 30%, var(--color-surface));
  }

  .cell.incomplete {
    background: color-mix(in srgb, var(--color-warning) 20%, var(--color-surface));
  }

  .cell.selected {
    border-color: var(--color-accent);
    box-shadow: var(--shadow-sm);
  }

  .dot {
    position: absolute;
    bottom: 4px;
    width: 4px;
    height: 4px;
    border-radius: var(--radius-full);
    background: var(--color-warning);
  }
</style>
