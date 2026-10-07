<script lang="ts">
  import { onMount } from 'svelte';
  import { animate } from 'motion';
  import Button from '@/components/Button.svelte';
  import Card from '@/components/Card.svelte';
  import {
    prefersReducedMotion,
    projectMomentum,
    rubberband,
    springMomentum,
    springSheet,
    springUi,
  } from '@/design/motion';

  let sheetOpen = $state(false);
  let sheetEl: HTMLDivElement | undefined = $state();
  let trackEl: HTMLDivElement | undefined = $state();
  let thumbEl: HTMLDivElement | undefined = $state();

  let dragY = $state(0);
  let dragging = $state(false);
  let pointerId: number | null = null;
  let grabOffset = 0;
  const history: { t: number; y: number }[] = [];

  function openSheet() {
    sheetOpen = true;
    requestAnimationFrame(() => {
      if (!sheetEl) return;
      if (prefersReducedMotion()) {
        sheetEl.style.opacity = '1';
        sheetEl.style.transform = 'translateY(0)';
        return;
      }
      animate(sheetEl, { y: [320, 0], opacity: [0, 1] }, springSheet);
    });
  }

  function closeSheet() {
    if (!sheetEl) {
      sheetOpen = false;
      return;
    }
    if (prefersReducedMotion()) {
      sheetOpen = false;
      return;
    }
    animate(sheetEl, { y: 320, opacity: 0 }, springUi).finished.then(() => {
      sheetOpen = false;
      if (sheetEl) {
        sheetEl.style.transform = '';
        sheetEl.style.opacity = '';
      }
    });
  }

  function velocityFromHistory(): number {
    if (history.length < 2) return 0;
    const a = history[history.length - 2];
    const b = history[history.length - 1];
    const dt = (b.t - a.t) / 1000;
    if (dt <= 0) return 0;
    return (b.y - a.y) / dt;
  }

  function onSheetPointerDown(e: PointerEvent) {
    if (!sheetEl) return;
    pointerId = e.pointerId;
    dragging = true;
    grabOffset = e.clientY - sheetEl.getBoundingClientRect().top;
    sheetEl.setPointerCapture(e.pointerId);
    history.length = 0;
    history.push({ t: performance.now(), y: e.clientY });
  }

  function onSheetPointerMove(e: PointerEvent) {
    if (!dragging || !sheetEl || e.pointerId !== pointerId) return;
    const raw = Math.max(0, e.clientY - grabOffset);
    const y = rubberband(raw, 400);
    dragY = y;
    sheetEl.style.transform = `translateY(${y}px)`;
    history.push({ t: performance.now(), y: e.clientY });
    if (history.length > 8) history.shift();
  }

  function onSheetPointerUp(e: PointerEvent) {
    if (!dragging || !sheetEl || e.pointerId !== pointerId) return;
    dragging = false;
    sheetEl.releasePointerCapture(e.pointerId);
    pointerId = null;
    const vy = velocityFromHistory();
    const projected = dragY + projectMomentum(vy);
    if (projected > 120 || vy > 400) {
      closeSheet();
    } else {
      animate(sheetEl, { y: 0 }, { ...springMomentum, velocity: vy }).finished.then(() => {
        dragY = 0;
        if (sheetEl) sheetEl.style.transform = '';
      });
    }
  }

  // Slider thumb — 1:1 drag with press feedback
  let thumbX = $state(24);
  let thumbDragging = $state(false);

  function onThumbDown(e: PointerEvent) {
    if (!trackEl || !thumbEl) return;
    thumbDragging = true;
    thumbEl.setPointerCapture(e.pointerId);
  }

  function onThumbMove(e: PointerEvent) {
    if (!thumbDragging || !trackEl || !thumbEl) return;
    const rect = trackEl.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const clamped = Math.max(12, Math.min(rect.width - 12, x));
    thumbX = clamped;
    thumbEl.style.transform = `translateX(${clamped - 12}px)`;
  }

  function onThumbUp(e: PointerEvent) {
    if (!thumbDragging || !thumbEl) return;
    thumbDragging = false;
    thumbEl.releasePointerCapture(e.pointerId);
    const rect = trackEl?.getBoundingClientRect();
    const target = rect && thumbX > rect.width / 2 ? rect.width - 24 : 12;
    animate(thumbEl, { x: target - 12 }, springUi);
    thumbX = target;
  }

  onMount(() => {
    // noop — refs bound via bind:this
  });
</script>

<div class="lab">
  <header class="lab-header">
    <p class="text-overline">Dev only</p>
    <h1 class="text-title-1">Interaction lab</h1>
    <p class="text-body sub">
      Springs, pointer-down feedback, sheet physics, and rubber-banding — tuned before real screens ship.
    </p>
  </header>

  <div class="grid">
    <Card title="Buttons" subtitle="Feedback on press, not release">
      <div class="row">
        <Button variant="primary">Primary</Button>
        <Button variant="secondary">Secondary</Button>
        <Button variant="ghost">Ghost</Button>
      </div>
    </Card>

    <Card title="Toggle track" subtitle="1:1 pointer capture">
      <div class="track" bind:this={trackEl}>
        <div
          class="thumb"
          bind:this={thumbEl}
          role="slider"
          aria-valuenow={Math.round(thumbX)}
          tabindex="0"
          onpointerdown={onThumbDown}
          onpointermove={onThumbMove}
          onpointerup={onThumbUp}
          onpointercancel={onThumbUp}
        ></div>
      </div>
    </Card>

    <Card title="Bottom sheet" subtitle="Velocity handoff + dismiss projection">
      <Button variant="primary" onclick={openSheet}>Open sheet</Button>
      <p class="text-caption hint">Drag down to dismiss; flick uses momentum projection.</p>
    </Card>
  </div>
</div>

{#if sheetOpen}
  <div class="scrim" role="presentation" onclick={closeSheet}></div>
  <div
    class="sheet"
    bind:this={sheetEl}
    role="dialog"
    aria-modal="true"
    aria-label="Demo sheet"
    tabindex="-1"
    style="transform: translateY(320px); opacity: 0"
    onpointerdown={onSheetPointerDown}
    onpointermove={onSheetPointerMove}
    onpointerup={onSheetPointerUp}
    onpointercancel={onSheetPointerUp}
  >
    <div class="sheet-grab" aria-hidden="true"></div>
    <h2 class="text-headline">Sheet</h2>
    <p class="text-body">
      Interruptible motion: grab mid-animation and reverse without a jump. Release velocity continues into the spring.
    </p>
    <Button variant="secondary" onclick={closeSheet}>Close</Button>
  </div>
{/if}

<style>
  .lab {
    padding: var(--space-6);
    max-width: 900px;
    margin: 0 auto;
  }

  .lab-header {
    margin-bottom: var(--space-8);
  }

  .sub {
    color: var(--color-text-secondary);
    max-width: 50ch;
  }

  .grid {
    display: grid;
    gap: var(--space-6);
  }

  .row {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-3);
  }

  .track {
    position: relative;
    height: 44px;
    border-radius: var(--radius-full);
    background: var(--color-surface);
    border: 1px solid var(--color-border-subtle);
  }

  .thumb {
    position: absolute;
    left: 0;
    top: 6px;
    width: 32px;
    height: 32px;
    border-radius: var(--radius-full);
    background: var(--color-accent);
    box-shadow: var(--shadow-md);
    touch-action: none;
    cursor: grab;
    will-change: transform;
  }

  .thumb:active {
    cursor: grabbing;
    transform: scale(0.97);
  }

  .hint {
    margin-top: var(--space-3);
  }

  .scrim {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.45);
    backdrop-filter: blur(4px);
    z-index: 40;
    animation: fade-in var(--duration-fast) var(--ease-out-quart);
  }

  @keyframes fade-in {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  .sheet {
    position: fixed;
    left: 50%;
    bottom: 0;
    transform: translateX(-50%);
    width: min(480px, calc(100% - 2rem));
    padding: var(--space-6);
    padding-top: var(--space-4);
    background: var(--material-chrome);
    backdrop-filter: blur(var(--material-blur)) saturate(var(--material-saturate));
    border: 1px solid var(--color-border-strong);
    border-bottom: none;
    border-radius: var(--radius-xl) var(--radius-xl) 0 0;
    box-shadow: var(--shadow-lg);
    z-index: 50;
    touch-action: none;
  }

  .sheet-grab {
    width: 36px;
    height: 4px;
    border-radius: var(--radius-full);
    background: var(--color-border-strong);
    margin: 0 auto var(--space-4);
  }

  @media (prefers-reduced-motion: reduce) {
    .scrim {
      animation: none;
    }
  }

  @media (prefers-reduced-transparency: reduce) {
    .sheet,
    .scrim {
      backdrop-filter: none;
    }
    .sheet {
      background: var(--color-bg-elevated);
    }
  }
</style>
