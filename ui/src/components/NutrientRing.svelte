<script lang="ts">
  type Props = {
    label: string;
    value: number | null;
    target: number;
    unit?: string;
    accent?: string;
    size?: number;
  };

  let {
    label,
    value,
    target,
    unit = '',
    accent = 'var(--color-accent)',
    size = 88,
  }: Props = $props();

  const stroke = 8;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;

  const progress = $derived(
    value === null || target <= 0 ? 0 : Math.min(1, value / target),
  );
  const dashOffset = $derived(circumference * (1 - progress));

  function displayValue(v: number | null): string {
    if (v === null) return '—';
    if (unit === 'kcal') return String(Math.round(v));
    return v % 1 === 0 ? String(v) : v.toFixed(1);
  }
</script>

<div class="ring" style:--ring-accent={accent} style:width="{size}px" style:height="{size}px">
  <svg width={size} height={size} viewBox="0 0 {size} {size}" aria-hidden="true">
    <circle
      class="track"
      cx={size / 2}
      cy={size / 2}
      r={radius}
      fill="none"
      stroke-width={stroke}
    />
    <circle
      class="fill"
      cx={size / 2}
      cy={size / 2}
      r={radius}
      fill="none"
      stroke-width={stroke}
      stroke-dasharray={circumference}
      stroke-dashoffset={dashOffset}
      transform="rotate(-90 {size / 2} {size / 2})"
    />
  </svg>
  <div class="center">
    <span class="value text-title-3">{displayValue(value)}</span>
    <span class="caption text-caption">{label}</span>
  </div>
</div>

<style>
  .ring {
    position: relative;
    flex-shrink: 0;
  }

  .track {
    stroke: var(--color-border-subtle);
  }

  .fill {
    stroke: var(--ring-accent);
    stroke-linecap: round;
    transition: stroke-dashoffset var(--duration-fast) var(--ease-out-quart);
  }

  .center {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0;
    pointer-events: none;
  }

  .value {
    font-size: 1rem;
    line-height: 1.1;
  }

  .caption {
    color: var(--color-text-tertiary);
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
</style>
