<script lang="ts">
  import { onMount } from 'svelte';
  import Chrome from '@/components/Chrome.svelte';
  import { parseRoute, type Route } from '@/lib/routes';
  import Home from '@/screens/Home.svelte';
  import Gallery from '@/screens/gallery/Gallery.svelte';

  let route: Route = $state('home');

  function syncRoute() {
    route = parseRoute(location.hash);
  }

  function navigate(next: Route) {
    location.hash = next === 'gallery' ? '/gallery' : '/';
  }

  onMount(() => {
    syncRoute();
    window.addEventListener('hashchange', syncRoute);
    return () => window.removeEventListener('hashchange', syncRoute);
  });
</script>

<Chrome {route} onNavigate={navigate} />
{#if route === 'gallery' && import.meta.env.DEV}
  <Gallery />
{:else}
  <Home />
{/if}
