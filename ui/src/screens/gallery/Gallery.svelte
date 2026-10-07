<script lang="ts">
  import ComponentGallery from './ComponentGallery.svelte';
  import InteractionLab from './InteractionLab.svelte';
</script>

<div class="gallery-page">
  <ComponentGallery />
  <InteractionLab />
</div>

<style>
  .gallery-page {
    flex: 1;
    overflow: auto;
    padding-bottom: var(--space-12);
  }
</style>
