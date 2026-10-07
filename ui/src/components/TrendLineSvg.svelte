<script lang="ts">
  type Props = {
    dates: string[];
    values: (number | null)[];
    secondary?: (number | null)[];
    label: string;
    unit?: string;
    width?: number;
    height?: number;
    color?: string;
    secondaryColor?: string;
  };

  let {
    dates,
    values,
    secondary = [],
    label,
    unit = '',
    width = 320,
    height = 120,
    color = 'var(--color-accent)',
    secondaryColor = 'var(--color-text-secondary)',
  }: Props = $props();

  const pad = { top: 12, right: 8, bottom: 20, left: 8 };
  const innerW = $derived(width - pad.left - pad.right);
  const innerH = $derived(height - pad.top - pad.bottom);

  const numeric = $derived(
    [...values, ...secondary].filter((v): v is number => v !== null && Number.isFinite(v)),
  );

  const ymin = $derived(numeric.length ? Math.min(...numeric) : 0);
  const ymax = $derived(numeric.length ? Math.max(...numeric) : 1);
  const span = $derived(ymax - ymin || 1);

  function xAt(i: number): number {
    if (dates.length <= 1) return pad.left + innerW / 2;
    return pad.left + (i / (dates.length - 1)) * innerW;
  }

  function yAt(v: number | null): number | null {
    if (v === null || !Number.isFinite(v)) return null;
    const t = (v - ymin) / span;
    return pad.top + innerH - t * innerH;
  }

  function polyline(points: (number | null)[]): string {
    const parts: string[] = [];
    points.forEach((v, i) => {
      const y = yAt(v);
      if (y === null) return;
      parts.push(`${xAt(i)},${y}`);
    });
    return parts.join(' ');
  }
</script>

<svg {width} {height} role="img" aria-label="{label} trend">
  <text x="0" y="10" class="title">{label}{unit ? ` (${unit})` : ''}</text>
  <line
    x1={pad.left}
    y1={pad.top + innerH}
    x2={pad.left + innerW}
    y2={pad.top + innerH}
    class="axis"
  />
  {#if values.some((v) => v !== null)}
    <polyline points={polyline(values)} class="line" style="stroke: {color}" fill="none" />
  {/if}
  {#if secondary.some((v) => v !== null)}
    <polyline
      points={polyline(secondary)}
      class="line secondary"
      style="stroke: {secondaryColor}"
      fill="none"
    />
  {/if}
</svg>

<style>
  .title {
    font-size: 0.75rem;
    fill: var(--color-text-secondary);
  }

  .axis {
    stroke: var(--color-border-subtle);
    stroke-width: 1;
  }

  .line {
    stroke-width: 2;
    stroke-linecap: round;
    stroke-linejoin: round;
  }

  .secondary {
    stroke-width: 1.5;
    stroke-dasharray: 4 3;
    opacity: 0.85;
  }
</style>
