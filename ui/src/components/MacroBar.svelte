<script lang="ts">
  type Props = {
    label: string;
    value: number | null;
    target: number;
    remaining: number | null;
    unit: string;
    accent?: string;
  };

  let {
    label,
    value,
    target,
    remaining,
    unit,
    accent = 'var(--color-accent)',
  }: Props = $props();

  const progress = $derived(
    value === null || target <= 0 ? 0 : Math.min(1, value / target),
  );

  function fmt(n: number | null): string {
    if (n === null) return '—';
    return n % 1 === 0 ? String(n) : n.toFixed(1);
  }
</script>

<div class="macro-bar">
  <div class="row">
    <span class="label">{label}</span>
    <span class="nums text-caption">
      <span>{fmt(value)}{unit}</span>
      <span class="sep">/</span>
      <span>{fmt(target)}{unit}</span>
      <span class="remain">({fmt(remaining)} left)</span>
    </span>
  </div>
  <div class="track" role="presentation">
    <div class="fill" style:width="{progress * 100}%" style:background={accent}></div>
  </div>
</div>

<style>
  .macro-bar {
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
  }

  .row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: var(--space-2);
  }

  .label {
    font-weight: 600;
    font-size: 0.875rem;
  }

  .nums {
    color: var(--color-text-secondary);
  }

  .sep {
    margin: 0 0.15rem;
    opacity: 0.5;
  }

  .remain {
    margin-left: var(--space-2);
    color: var(--color-text-tertiary);
  }

  .track {
    height: 6px;
    border-radius: var(--radius-full);
    background: var(--color-border-subtle);
    overflow: hidden;
  }

  .fill {
    height: 100%;
    border-radius: inherit;
    transition: width var(--duration-fast) var(--ease-out-quart);
  }
</style>
