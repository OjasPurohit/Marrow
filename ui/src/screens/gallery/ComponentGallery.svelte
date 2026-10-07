<script lang="ts">
  import Button from '@/components/Button.svelte';
  import Card from '@/components/Card.svelte';
</script>

<section class="gallery">
  <h2 class="text-title-2">Components</h2>
  <div class="stack">
    <Card title="Typography" subtitle="Optical sizing & tracking">
      <p class="text-display sample">Display</p>
      <p class="text-title-1 sample">Title 1</p>
      <p class="text-headline sample">Headline</p>
      <p class="text-body sample">Body — comfortable leading for nutrition copy.</p>
      <p class="text-caption sample">Caption secondary</p>
      <p class="text-overline sample">Overline</p>
    </Card>

    <Card title="Surfaces" subtitle="Elevated cards & materials">
      <div class="swatches">
        <div class="swatch elevated">Elevated</div>
        <div class="swatch glass">Glass chrome</div>
        <div class="swatch accent">Accent</div>
      </div>
    </Card>

    <Card title="Actions">
      <div class="row">
        <Button variant="primary">Save</Button>
        <Button variant="secondary">Cancel</Button>
        <Button variant="ghost">Learn more</Button>
      </div>
    </Card>
  </div>
</section>

<style>
  .gallery {
    padding: var(--space-6);
    max-width: 900px;
    margin: 0 auto;
  }

  .stack {
    display: flex;
    flex-direction: column;
    gap: var(--space-6);
    margin-top: var(--space-4);
  }

  .sample {
    margin: var(--space-2) 0;
  }

  .swatches {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: var(--space-3);
  }

  .swatch {
    padding: var(--space-6) var(--space-4);
    border-radius: var(--radius-md);
    text-align: center;
    font-size: 0.8125rem;
    font-weight: 600;
  }

  .elevated {
    background: var(--color-bg-elevated);
    border: 1px solid var(--color-border-subtle);
  }

  .glass {
    background: var(--material-chrome);
    backdrop-filter: blur(var(--material-blur));
    border: 1px solid var(--color-border-subtle);
  }

  .accent {
    background: var(--color-accent-muted);
    color: var(--color-accent);
  }

  .row {
    display: flex;
    gap: var(--space-3);
    flex-wrap: wrap;
  }
</style>
