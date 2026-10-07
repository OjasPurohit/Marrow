<script lang="ts">
  type Props = {
    proteinPct: number | null;
    carbsPct: number | null;
    fatPct: number | null;
    size?: number;
  };

  let { proteinPct, carbsPct, fatPct, size = 120 }: Props = $props();

  const segments = $derived(() => {
    const p = proteinPct ?? 0;
    const c = carbsPct ?? 0;
    const f = fatPct ?? 0;
    const total = p + c + f;
    if (total <= 0) return [];
    const r = size / 2 - 8;
    const cx = size / 2;
    const cy = size / 2;
    let angle = -90;
    const colors = [
      { pct: p / total, color: 'var(--color-success)', label: 'Protein' },
      { pct: c / total, color: 'var(--color-warning)', label: 'Carbs' },
      { pct: f / total, color: '#8ab4f8', label: 'Fat' },
    ];
    return colors.map((seg) => {
      const sweep = seg.pct * 360;
      const start = angle;
      angle += sweep;
      const end = angle;
      const large = sweep > 180 ? 1 : 0;
      const x1 = cx + r * Math.cos((Math.PI * start) / 180);
      const y1 = cy + r * Math.sin((Math.PI * start) / 180);
      const x2 = cx + r * Math.cos((Math.PI * end) / 180);
      const y2 = cy + r * Math.sin((Math.PI * end) / 180);
      const d =
        sweep >= 359.9
          ? `M ${cx} ${cy - r} A ${r} ${r} 0 1 1 ${cx - 0.01} ${cy - r}`
          : `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2} Z`;
      return { ...seg, d };
    });
  });
</script>

<svg
  width={size}
  height={size}
  viewBox="0 0 {size} {size}"
  role="img"
  aria-label="Macro calorie split"
>
  <circle cx={size / 2} cy={size / 2} r={size / 2 - 4} fill="var(--color-surface)" />
  {#each segments() as seg}
    <path d={seg.d} fill={seg.color} opacity="0.92" />
  {/each}
  <circle cx={size / 2} cy={size / 2} r={size / 4} fill="var(--color-bg-elevated)" />
</svg>

<div class="legend text-caption">
  <span><i class="dot protein"></i> P {proteinPct ?? '—'}%</span>
  <span><i class="dot carbs"></i> C {carbsPct ?? '—'}%</span>
  <span><i class="dot fat"></i> F {fatPct ?? '—'}%</span>
</div>

<style>
  .legend {
    display: flex;
    gap: var(--space-3);
    justify-content: center;
    margin-top: var(--space-2);
    color: var(--color-text-secondary);
  }

  .dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: var(--radius-full);
    margin-right: var(--space-1);
    vertical-align: middle;
  }

  .protein {
    background: var(--color-success);
  }

  .carbs {
    background: var(--color-warning);
  }

  .fat {
    background: #8ab4f8;
  }
</style>
