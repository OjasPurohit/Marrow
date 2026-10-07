<script lang="ts">
  type Variant = 'primary' | 'secondary' | 'ghost';
  type Size = 'md' | 'lg';

  interface Props {
    variant?: Variant;
    size?: Size;
    disabled?: boolean;
    type?: 'button' | 'submit';
    onclick?: (e: MouseEvent) => void;
    children?: import('svelte').Snippet;
  }

  let {
    variant = 'primary',
    size = 'md',
    disabled = false,
    type = 'button',
    onclick,
    children,
  }: Props = $props();
</script>

<button {type} class="btn {variant} {size}" {disabled} {onclick}>
  {#if children}
    {@render children()}
  {/if}
</button>

<style>
  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-2);
    border-radius: var(--radius-md);
    font-weight: 600;
    letter-spacing: 0.005em;
    transition: background var(--duration-fast) var(--ease-out-quart),
      transform var(--duration-instant) var(--ease-out-quart),
      box-shadow var(--duration-fast) var(--ease-out-quart);
    border: 1px solid transparent;
  }

  .btn:active:not(:disabled) {
    transform: scale(0.97);
  }

  .btn:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }

  .md {
    padding: var(--space-2) var(--space-4);
    font-size: 0.9375rem;
  }

  .lg {
    padding: var(--space-3) var(--space-6);
    font-size: 1rem;
  }

  .primary {
    background: var(--color-accent);
    color: #1a120c;
    box-shadow: 0 1px 0 rgba(255, 255, 255, 0.2) inset, var(--shadow-sm);
  }

  .primary:hover:not(:disabled) {
    background: var(--color-accent-press);
  }

  .secondary {
    background: var(--color-surface);
    border-color: var(--color-border-subtle);
    color: var(--color-text);
  }

  .secondary:hover:not(:disabled) {
    background: var(--color-surface-hover);
  }

  .ghost {
    color: var(--color-accent);
  }

  .ghost:hover:not(:disabled) {
    background: var(--color-accent-muted);
  }
</style>
