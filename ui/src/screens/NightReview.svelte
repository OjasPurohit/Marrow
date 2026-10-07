<script lang="ts">
  import { onMount } from 'svelte';
  import Card from '@/components/Card.svelte';
  import MacroBar from '@/components/MacroBar.svelte';
  import MacroSplitSvg from '@/components/MacroSplitSvg.svelte';
  import MicroBarSvg from '@/components/MicroBarSvg.svelte';
  import NutrientRing from '@/components/NutrientRing.svelte';
  import { getNightReview, type NightReviewResponse } from '@/lib/nightReview';
  import { formatKcal } from '@/lib/parseQuantity';

  let review: NightReviewResponse | null = $state(null);
  let error = $state<string | null>(null);
  let loading = $state(true);

  const microKeys = new Set([
    'fiber_g',
    'sugar_g',
    'sodium_mg',
    'potassium_mg',
    'calcium_mg',
    'iron_mg',
    'magnesium_mg',
    'phosphorus_mg',
    'zinc_mg',
    'selenium_ug',
    'vitamin_a_ug',
    'vitamin_c_mg',
    'vitamin_d_ug',
    'vitamin_e_mg',
    'vitamin_k_ug',
    'thiamin_mg',
    'riboflavin_mg',
    'niacin_mg',
    'vitamin_b6_mg',
    'folate_ug',
    'vitamin_b12_ug',
  ]);

  function balanceLabel(status: string | null | undefined): string {
    if (status === 'DEFICIT') return 'Calorie deficit';
    if (status === 'SURPLUS') return 'Calorie surplus';
    if (status === 'ON_TARGET') return 'On target';
    return 'No verdict';
  }

  onMount(async () => {
    try {
      review = await getNightReview();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Could not load night review';
    } finally {
      loading = false;
    }
  });

  const macros = $derived(review?.macro_totals);
  const targets = $derived(review?.targets ?? {});
  const balance = $derived(review?.energy_balance);
  const microRows = $derived(
    (review?.nutrients ?? []).filter((r) => microKeys.has(r.key) || r.target != null),
  );
  const flagged = $derived(review?.flagged ?? []);
</script>

<main class="page">
  <header class="hero">
    <div>
      <p class="text-caption">Night review</p>
      <h1 class="text-title-1">{review?.log_date ?? 'Today'}</h1>
    </div>
    <a class="back text-caption" href="#/">← Today</a>
  </header>

  {#if loading}
    <p class="text-caption">Loading day report…</p>
  {:else if error}
    <p class="error">{error}</p>
  {:else if review}
    <section class="verdict" data-status={balance?.status ?? 'none'}>
      <h2 class="text-title-2">{balanceLabel(balance?.status)}</h2>
      {#if balance?.energy_delta_kcal != null}
        <p class="delta">
          {balance.energy_delta_kcal > 0 ? '+' : ''}{Math.round(balance.energy_delta_kcal)} kcal vs target
        </p>
      {/if}
      {#if review.estimated_confidence.estimated_pct_of_known != null}
        <p class="text-caption est">
          {review.estimated_confidence.estimated_pct_of_known}% of logged calories are estimated-confidence matches.
        </p>
      {/if}
    </section>

    {#if review.summary_lines.length}
      <Card title="Summary" subtitle="Rule-based recap (Groq optional in M8)">
        <ul class="summary">
          {#each review.summary_lines as line}
            <li>{line}</li>
          {/each}
        </ul>
      </Card>
    {/if}

    {#if flagged.length}
      <Card title="Flags" subtitle="Lows and highs vs your targets">
        <ul class="flags">
          {#each flagged as row}
            <li class={row.flag ?? ''}>
              <strong>{row.label}</strong>
              {#if row.pct_of_target != null}
                — {row.pct_of_target}% of target
              {:else}
                — no data
              {/if}
            </li>
          {/each}
        </ul>
      </Card>
    {/if}

    <section class="macros">
      <h2 class="text-title-2">Macros</h2>
      <div class="macro-grid">
        <div class="rings">
          <NutrientRing
            label="kcal"
            value={macros?.energy_kcal ?? null}
            target={targets.energy_kcal ?? 2200}
            accent="var(--color-accent)"
          />
          <MacroSplitSvg
            proteinPct={review.macro_split.protein_pct}
            carbsPct={review.macro_split.carbs_pct}
            fatPct={review.macro_split.fat_pct}
          />
        </div>
        <div class="bars">
          <MacroBar
            label="Protein"
            value={macros?.protein_g ?? null}
            target={targets.protein_g ?? 150}
            remaining={null}
            unit=" g"
            accent="var(--color-success)"
          />
          <MacroBar
            label="Carbs"
            value={macros?.carbs_g ?? null}
            target={targets.carbs_g ?? 220}
            remaining={null}
            unit=" g"
            accent="var(--color-warning)"
          />
          <MacroBar
            label="Fat"
            value={macros?.fat_g ?? null}
            target={targets.fat_g ?? 70}
            remaining={null}
            unit=" g"
            accent="#8ab4f8"
          />
        </div>
      </div>
    </section>

    <section class="micros">
      <h2 class="text-title-2">Micronutrients</h2>
      <p class="text-caption note">
        Missing values show as <em>no data</em>. Partial totals only sum foods with known values for that nutrient.
      </p>
      <div class="micro-list">
        {#each microRows as row (row.key)}
          <div class="micro-row">
            <MicroBarSvg
              label={row.label}
              consumed={row.consumed}
              target={row.target}
              pctOfTarget={row.pct_of_target}
              unit={row.unit}
              flag={row.flag}
              partial={row.partial_total}
            />
            {#if row.top_contributors.length}
              <p class="contributors text-caption">
                Top: {row.top_contributors.map((c) => `${c.food_name} (${c.amount}${c.unit})`).join(', ')}
              </p>
            {/if}
          </div>
        {/each}
      </div>
    </section>

    <p class="text-caption footer">
      {review.entry_count} entries · {formatKcal(macros?.energy_kcal ?? null)} kcal logged
    </p>
  {/if}
</main>

<style>
  .page {
    max-width: 720px;
    margin: 0 auto;
    padding: var(--space-6);
    display: flex;
    flex-direction: column;
    gap: var(--space-6);
  }

  .hero {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: var(--space-4);
  }

  .back {
    color: var(--color-accent);
    text-decoration: none;
  }

  .verdict {
    padding: var(--space-5);
    border-radius: var(--radius-lg);
    background: var(--color-bg-elevated);
    border: 1px solid var(--color-border-subtle);
    text-align: center;
  }

  .verdict[data-status='DEFICIT'] {
    border-color: var(--color-warning);
  }

  .verdict[data-status='SURPLUS'] {
    border-color: var(--color-danger, #e57373);
  }

  .verdict[data-status='ON_TARGET'] {
    border-color: var(--color-success);
  }

  .delta {
    font-size: 1.25rem;
    font-weight: 600;
    margin-top: var(--space-2);
  }

  .est {
    margin-top: var(--space-2);
    opacity: 0.85;
  }

  .summary,
  .flags {
    margin: 0;
    padding-left: var(--space-5);
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .flags .low {
    color: var(--color-warning);
  }

  .flags .high {
    color: var(--color-danger, #e57373);
  }

  .macro-grid {
    display: grid;
    gap: var(--space-5);
  }

  @media (min-width: 640px) {
    .macro-grid {
      grid-template-columns: 1fr 1fr;
      align-items: start;
    }
  }

  .rings {
    display: flex;
    gap: var(--space-4);
    align-items: center;
    justify-content: center;
  }

  .bars {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  .micro-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
  }

  .micro-row {
    padding-bottom: var(--space-2);
    border-bottom: 1px solid var(--color-border-subtle);
  }

  .contributors {
    margin: var(--space-1) 0 0;
    padding-left: 100px;
  }

  .note {
    margin-bottom: var(--space-3);
  }

  .footer {
    text-align: center;
    opacity: 0.7;
  }

  .error {
    color: var(--color-danger, #e57373);
  }
</style>
