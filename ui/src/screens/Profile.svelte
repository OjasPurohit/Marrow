<script lang="ts">
  import { onMount } from 'svelte';
  import Card from '@/components/Card.svelte';
  import { getUserProfile, type UserProfile } from '@/lib/profile';

  let profile = $state<UserProfile | null>(null);

  onMount(async () => {
    profile = await getUserProfile();
  });
</script>

<main class="profile">
  <h1 class="text-display">Profile</h1>
  {#if profile?.onboarding_completed}
    <Card title="Targets" subtitle="From your onboarding plan">
      <dl class="facts">
        <div><dt>Goal</dt><dd>{profile.goal}</dd></div>
        <div><dt>Activity</dt><dd>{profile.activity_level}</dd></div>
        <div><dt>Tolerance</dt><dd>±{profile.calorie_tolerance_pct ?? 5}%</dd></div>
        <div><dt>Daily kcal</dt><dd>{profile.macro_targets?.default?.energy_kcal}</dd></div>
        <div><dt>Protein</dt><dd>{profile.macro_targets?.default?.protein_g} g</dd></div>
      </dl>
      <p class="text-caption disclaimer">{profile.disclaimer}</p>
    </Card>
  {:else}
    <p class="text-body">Complete onboarding from the Today screen to set targets.</p>
  {/if}
</main>

<style>
  .profile {
    max-width: 640px;
    margin: 0 auto;
    padding: var(--space-6);
  }

  .facts {
    display: grid;
    gap: var(--space-2);
  }

  .facts div {
    display: flex;
    justify-content: space-between;
    gap: var(--space-4);
  }

  dt {
    color: var(--color-text-secondary);
  }

  .disclaimer {
    margin-top: var(--space-4);
  }
</style>
