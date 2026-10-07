<script lang="ts">
  import { onMount } from 'svelte';
  import Chrome from '@/components/Chrome.svelte';
  import { parseRoute, type Route } from '@/lib/routes';
  import Home from '@/screens/Home.svelte';
  import Foods from '@/screens/Foods.svelte';
  import Profile from '@/screens/Profile.svelte';
  import Onboarding from '@/screens/Onboarding.svelte';
  import Gallery from '@/screens/gallery/Gallery.svelte';
  import { ensureProfileBridge, getUserProfile } from '@/lib/profile';

  let route: Route = $state('home');
  let showOnboarding = $state(false);
  let profileChecked = $state(false);

  function syncRoute() {
    route = parseRoute(location.hash);
  }

  function navigate(next: Route) {
    if (next === 'gallery') location.hash = '/gallery';
    else if (next === 'foods') location.hash = '/foods';
    else if (next === 'profile') location.hash = '/profile';
    else location.hash = '/';
  }

  async function refreshProfileGate() {
    await ensureProfileBridge();
    const profile = await getUserProfile();
    showOnboarding = !profile.onboarding_completed;
    profileChecked = true;
  }

  onMount(() => {
    syncRoute();
    window.addEventListener('hashchange', syncRoute);
    refreshProfileGate();
    return () => window.removeEventListener('hashchange', syncRoute);
  });
</script>

<Chrome {route} onNavigate={navigate} />
{#if showOnboarding}
  <Onboarding
    onComplete={() => {
      showOnboarding = false;
      profileChecked = true;
    }}
  />
{:else if route === 'gallery' && import.meta.env.DEV}
  <Gallery />
{:else if route === 'foods'}
  <Foods />
{:else if route === 'profile'}
  <Profile />
{:else if profileChecked}
  <Home />
{/if}
