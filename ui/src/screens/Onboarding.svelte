<script lang="ts">
  import Button from '@/components/Button.svelte';
  import Card from '@/components/Card.svelte';
  import {
    completeOnboarding,
    previewMetabolicPlan,
    type MacroTargets,
    type MetabolicPlan,
  } from '@/lib/profile';

  interface Props {
    onComplete: () => void;
  }

  let { onComplete }: Props = $props();

  let step = $state(1);
  let error = $state<string | null>(null);
  let loading = $state(false);
  let plan = $state<MetabolicPlan | null>(null);

  let ageYears = $state(30);
  let sex = $state<'male' | 'female'>('male');
  let heightCm = $state(175);
  let weightKg = $state(72);
  let activity = $state('moderate');
  let goal = $state('maintain');
  let disclaimerOk = $state(false);

  let macros = $state<MacroTargets | null>(null);
  let tolerancePct = $state(5);
  let useSplit = $state(false);
  let gymWeekdays = $state<number[]>([0, 2, 4]);

  const weekdayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  function payloadBase() {
    return {
      age_years: ageYears,
      sex,
      height_cm: heightCm,
      weight_kg: weightKg,
      activity_level: activity,
      goal,
    };
  }

  async function goToTargets() {
    error = null;
    loading = true;
    try {
      plan = await previewMetabolicPlan(payloadBase());
      macros = { ...plan.suggested_default };
      step = 2;
    } catch (e) {
      error = e instanceof Error ? e.message : 'Could not compute plan';
    } finally {
      loading = false;
    }
  }

  function toggleGymDay(day: number) {
    if (gymWeekdays.includes(day)) {
      gymWeekdays = gymWeekdays.filter((d) => d !== day);
    } else {
      gymWeekdays = [...gymWeekdays, day].sort();
    }
  }

  async function finish() {
    if (!disclaimerOk) {
      error = 'Please acknowledge the disclaimer.';
      return;
    }
    if (!macros || !plan) return;
    error = null;
    loading = true;
    try {
      await completeOnboarding({
        ...payloadBase(),
        disclaimer_acknowledged: true,
        calorie_tolerance_pct: tolerancePct,
        use_split_day_targets: useSplit,
        gym_weekdays: useSplit ? gymWeekdays : [],
        macro_targets: {
          default: macros,
          gym: plan.suggested_gym,
          rest: plan.suggested_rest,
        },
      });
      onComplete();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Save failed';
    } finally {
      loading = false;
    }
  }
</script>

<div class="onboarding">
  <Card title="Welcome to Marrow" subtitle="Step {step} of 2 — goals & targets">
    {#if step === 1}
      <p class="text-body lede">Tell us about you so we can estimate calories and macros (Mifflin-St Jeor).</p>
      <div class="grid">
        <label>
          <span class="text-caption">Age</span>
          <input type="number" min="13" max="100" bind:value={ageYears} />
        </label>
        <label>
          <span class="text-caption">Sex</span>
          <select bind:value={sex}>
            <option value="male">Male</option>
            <option value="female">Female</option>
          </select>
        </label>
        <label>
          <span class="text-caption">Height (cm)</span>
          <input type="number" min="100" max="250" bind:value={heightCm} />
        </label>
        <label>
          <span class="text-caption">Weight (kg)</span>
          <input type="number" min="30" max="300" step="0.1" bind:value={weightKg} />
        </label>
        <label class="wide">
          <span class="text-caption">Activity</span>
          <select bind:value={activity}>
            <option value="sedentary">Sedentary</option>
            <option value="light">Light</option>
            <option value="moderate">Moderate</option>
            <option value="active">Active</option>
            <option value="very_active">Very active</option>
          </select>
        </label>
        <label class="wide">
          <span class="text-caption">Goal</span>
          <select bind:value={goal}>
            <option value="cut">Cut</option>
            <option value="maintain">Maintain</option>
            <option value="lean_bulk">Lean bulk</option>
          </select>
        </label>
      </div>
      <div class="actions">
        <Button onclick={goToTargets} disabled={loading}>{loading ? 'Calculating…' : 'Next: targets'}</Button>
      </div>
    {:else if macros && plan}
      <p class="text-caption">
        BMR {Math.round(plan.bmr_kcal)} kcal · TDEE {Math.round(plan.tdee_kcal)} kcal
      </p>
      {#each plan.warnings as w}
        <p class="warn text-caption">{w}</p>
      {/each}
      <div class="grid">
        <label>
          <span class="text-caption">Daily kcal</span>
          <input type="number" bind:value={macros.energy_kcal} />
        </label>
        <label>
          <span class="text-caption">Protein (g)</span>
          <input type="number" bind:value={macros.protein_g} />
        </label>
        <label>
          <span class="text-caption">Carbs (g)</span>
          <input type="number" bind:value={macros.carbs_g} />
        </label>
        <label>
          <span class="text-caption">Fat (g)</span>
          <input type="number" bind:value={macros.fat_g} />
        </label>
        <label>
          <span class="text-caption">Tolerance ±%</span>
          <input type="number" min="1" max="25" bind:value={tolerancePct} />
        </label>
      </div>
      <label class="split">
        <input type="checkbox" bind:checked={useSplit} />
        <span>Different targets on gym vs rest days</span>
      </label>
      {#if useSplit}
        <div class="weekdays">
          {#each weekdayLabels as label, i}
            <button
              type="button"
              class:selected={gymWeekdays.includes(i)}
              onclick={() => toggleGymDay(i)}
            >
              {label}
            </button>
          {/each}
        </div>
        <p class="text-caption">Gym days use +200 kcal suggestion ({plan.suggested_gym.energy_kcal} kcal).</p>
      {/if}
      <p class="disclaimer text-caption">{plan.disclaimer}</p>
      <label class="split">
        <input type="checkbox" bind:checked={disclaimerOk} />
        <span>I understand this is not medical advice</span>
      </label>
      <div class="actions">
        <Button variant="secondary" onclick={() => (step = 1)}>Back</Button>
        <Button onclick={finish} disabled={loading}>{loading ? 'Saving…' : 'Start tracking'}</Button>
      </div>
    {/if}
    {#if error}
      <p class="error text-caption">{error}</p>
    {/if}
  </Card>
</div>

<style>
  .onboarding {
    position: fixed;
    inset: 0;
    z-index: 100;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: var(--space-6);
    background: color-mix(in srgb, var(--color-bg) 92%, transparent);
    backdrop-filter: blur(8px);
  }

  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-4);
    margin: var(--space-4) 0;
  }

  .wide {
    grid-column: 1 / -1;
  }

  label {
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
  }

  input,
  select {
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-md);
    border: 1px solid var(--color-border-subtle);
    background: var(--color-surface);
  }

  .actions {
    display: flex;
    gap: var(--space-3);
    margin-top: var(--space-4);
  }

  .lede {
    margin-bottom: var(--space-2);
  }

  .warn {
    color: var(--color-warning);
  }

  .error {
    color: var(--color-danger);
    margin-top: var(--space-3);
  }

  .disclaimer {
    margin: var(--space-4) 0 var(--space-2);
    opacity: 0.85;
  }

  .split {
    flex-direction: row;
    align-items: center;
    gap: var(--space-2);
    margin-top: var(--space-3);
  }

  .weekdays {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2);
    margin-top: var(--space-2);
  }

  .weekdays button {
    padding: var(--space-1) var(--space-3);
    border-radius: var(--radius-full);
    border: 1px solid var(--color-border-subtle);
    background: var(--color-surface);
    cursor: pointer;
  }

  .weekdays button.selected {
    background: var(--color-accent);
    color: var(--color-on-accent);
    border-color: transparent;
  }
</style>
