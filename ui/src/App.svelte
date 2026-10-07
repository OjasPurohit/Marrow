<script lang="ts">
  import { onMount } from 'svelte';
  import Chrome from '@/components/Chrome.svelte';
  import { parseRoute, type Route } from '@/lib/routes';
  import Home from '@/screens/Home.svelte';
  import Foods from '@/screens/Foods.svelte';
  import Profile from '@/screens/Profile.svelte';
  import NightReview from '@/screens/NightReview.svelte';
  import History from '@/screens/History.svelte';
  import Trends from '@/screens/Trends.svelte';
  import Settings from '@/screens/Settings.svelte';
  import Onboarding from '@/screens/Onboarding.svelte';
  import Gallery from '@/screens/gallery/Gallery.svelte';
  import CommandPalette from '@/components/CommandPalette.svelte';
  import { applyUserSettings } from '@/lib/applyPreferences';
  import { ensureProfileBridge, getUserProfile } from '@/lib/profile';
  import { ensureSettingsBridge, getUserSettings } from '@/lib/settings';

  let route: Route = $state('home');
  let showOnboarding = $state(false);
  let profileChecked = $state(false);
  let paletteOpen = $state(false);

  function syncRoute() {
    route = parseRoute(location.hash);
  }

  function navigate(next: Route) {
    if (next === 'gallery') location.hash = '/gallery';
    else if (next === 'foods') location.hash = '/foods';
    else if (next === 'profile') location.hash = '/profile';
    else if (next === 'nightReview') location.hash = '/night-review';
    else if (next === 'history') location.hash = '/history';
    else if (next === 'trends') location.hash = '/trends';
    else if (next === 'settings') location.hash = '/settings';
    else location.hash = '/';
  }

  function openQuickLog() {
    navigate('home');
    requestAnimationFrame(() => {
      window.dispatchEvent(new CustomEvent('marrow-focus-quick-log'));
    });
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
    void ensureSettingsBridge().then(async () => {
      applyUserSettings(await getUserSettings());
    });
    const onKeys = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        paletteOpen = !paletteOpen;
      }
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'l') {
        event.preventDefault();
        openQuickLog();
      }
    };
    window.addEventListener('keydown', onKeys);
    return () => {
      window.removeEventListener('hashchange', syncRoute);
      window.removeEventListener('keydown', onKeys);
    };
  });
</script>

<CommandPalette
  open={paletteOpen}
  onClose={() => (paletteOpen = false)}
  onNavigate={navigate}
  onQuickLog={openQuickLog}
/>
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
{:else if route === 'settings'}
  <Settings />
{:else if route === 'nightReview' && profileChecked}
  <NightReview />
{:else if route === 'history' && profileChecked}
  <History />
{:else if route === 'trends' && profileChecked}
  <Trends />
{:else if profileChecked}
  <Home />
{/if}
