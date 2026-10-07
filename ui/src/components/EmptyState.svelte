<script lang="ts">
  interface Props {
    title: string;
    detail?: string;
    actionLabel?: string;
    onAction?: () => void;
  }

  let { title, detail, actionLabel, onAction }: Props = $props();
</script>

<div class="empty-state" role="status">
  <div class="glyph" aria-hidden="true"></div>
  <p class="title text-title-3">{title}</p>
  {#if detail}
    <p class="detail text-caption">{detail}</p>
  {/if}
  {#if actionLabel && onAction}
    <button type="button" class="action" onclick={onAction}>{actionLabel}</button>
  {/if}
</div>

<style>
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: var(--space-3);
    padding: var(--space-8) var(--space-4);
    border-radius: var(--radius-lg);
    background: var(--color-surface);
    border: 1px dashed var(--color-border-subtle);
  }

  .glyph {
    width: 3rem;
    height: 3rem;
    border-radius: var(--radius-full);
    background: linear-gradient(145deg, var(--color-accent-muted), transparent);
    border: 1px solid var(--color-border-subtle);
    box-shadow: var(--shadow-sm);
  }

  .title {
    margin: 0;
    color: var(--color-text);
  }

  .detail {
    margin: 0;
    max-width: 28rem;
    color: var(--color-text-secondary);
  }

  .action {
    margin-top: var(--space-2);
    padding: var(--space-2) var(--space-5);
    border-radius: var(--radius-full);
    background: var(--color-accent);
    color: #1a1208;
    font-weight: 600;
  }

  .action:hover {
    background: var(--color-accent-press);
  }

  .action:focus-visible {
    outline: 2px solid var(--color-accent);
    outline-offset: 2px;
  }
</style>
