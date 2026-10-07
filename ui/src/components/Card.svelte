<script lang="ts">
  interface Props {
    title?: string;
    subtitle?: string;
    children?: import('svelte').Snippet;
  }

  let { title, subtitle, children }: Props = $props();
</script>

<section class="card">
  {#if title}
    <header class="card-header">
      <h2 class="text-headline">{title}</h2>
      {#if subtitle}
        <p class="text-caption">{subtitle}</p>
      {/if}
    </header>
  {/if}
  <div class="card-body">
    {#if children}
      {@render children()}
    {/if}
  </div>
</section>

<style>
  .card {
    background: var(--color-bg-elevated);
    border: 1px solid var(--color-border-subtle);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md);
    overflow: hidden;
  }

  .card-header {
    padding: var(--space-5) var(--space-6) var(--space-2);
  }

  .card-header h2 {
    margin: 0;
  }

  .card-header p {
    margin: var(--space-1) 0 0;
  }

  .card-body {
    padding: var(--space-4) var(--space-6) var(--space-6);
  }
</style>
