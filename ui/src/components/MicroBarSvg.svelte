<script lang="ts">
  type Props = {
    label: string;
    consumed: number | null;
    target: number | null;
    pctOfTarget: number | null;
    unit: string;
    flag: 'low' | 'high' | null;
    partial: boolean;
    width?: number;
  };

  let {
    label,
    consumed,
    target,
    pctOfTarget,
    unit,
    flag,
    partial,
    width = 280,
  }: Props = $props();

  const barW = 160;
  const h = 28;

  const progress = $derived(
    pctOfTarget === null ? 0 : Math.min(1.5, pctOfTarget / 100),
  );

  const fillW = $derived(barW * Math.min(1, progress));

  const accent = $derived(
    flag === 'low'
      ? 'var(--color-warning)'
      : flag === 'high'
        ? 'var(--color-danger, #e57373)'
        : 'var(--color-accent)',
  );

  function fmt(n: number | null): string {
    if (n === null) return 'no data';
    return n % 1 === 0 ? String(n) : n.toFixed(1);
  }
</script>

<svg width={width} height={h} role="img" aria-label="{label} intake">
  <text x="0" y="12" class="label">{label}</text>
  <rect x="100" y="6" width={barW} height="8" rx="4" class="track" />
  {#if consumed !== null}
    <rect x="100" y="6" width={fillW} height="8" rx="4" fill={accent} />
    {#if target}
      <line
        x1={100 + barW * Math.min(1, 1)}
        x2={100 + barW * Math.min(1, 1)}
        y1="4"
        y2="16"
        class="target-mark"
      />
    {/if}
  {/if}
  <text x="100" y="26" class="meta">
    {fmt(consumed)}{unit !== 'kcal' ? ` ${unit}` : ' kcal'}
    {#if target}
      / {fmt(target)}{unit !== 'kcal' ? ` ${unit}` : ''}
    {/if}
    {#if pctOfTarget !== null}
      · {pctOfTarget}%
    {/if}
    {#if partial}
      · partial
    {/if}
  </text>
</svg>

<style>
  .label {
    font-size: 11px;
    fill: var(--color-text);
    font-weight: 500;
  }

  .track {
    fill: var(--color-surface);
  }

  .target-mark {
    stroke: var(--color-text-secondary);
    stroke-width: 1;
    opacity: 0.5;
  }

  .meta {
    font-size: 9px;
    fill: var(--color-text-secondary);
  }
</style>
