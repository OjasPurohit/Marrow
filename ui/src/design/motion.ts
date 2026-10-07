/**
 * Spring presets aligned with apple-design reference.
 * Motion library: bounce ≈ (1 - damping_ratio) flavor; duration ≈ response.
 */

export const springUi = {
  type: 'spring' as const,
  bounce: 0,
  duration: 0.4,
};

export const springSheet = {
  type: 'spring' as const,
  bounce: 0.2,
  duration: 0.3,
};

export const springMomentum = {
  type: 'spring' as const,
  bounce: 0.2,
  duration: 0.4,
};

/** Apple's exponential decay projection (px). */
export function projectMomentum(
  initialVelocityPxPerSec: number,
  decelerationRate = 0.998,
): number {
  const d = decelerationRate;
  return (initialVelocityPxPerSec / 1000) * d / (1 - d);
}

/** Rubber-band overshoot (apple-design). */
export function rubberband(overshoot: number, dimension: number, constant = 0.55): number {
  return (overshoot * dimension * constant) / (dimension + constant * Math.abs(overshoot));
}

export function prefersReducedMotion(): boolean {
  if (typeof document !== 'undefined') {
    if (document.documentElement.dataset.reducedMotion === 'true') return true;
  }
  return (
    typeof matchMedia !== 'undefined' &&
    matchMedia('(prefers-reduced-motion: reduce)').matches
  );
}

/** Spring preset that collapses to a short tween when reduced motion is on. */
export function motionSpring(
  preset: { type: 'spring'; bounce: number; duration: number },
): { type: 'spring'; bounce: number; duration: number } | { duration: number } {
  if (prefersReducedMotion()) {
    return { duration: 0.01 };
  }
  return preset;
}
