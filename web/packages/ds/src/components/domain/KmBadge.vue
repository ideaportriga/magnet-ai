<script setup lang="ts">
/**
 * `<km-badge>` — small inline label. Drop-in over `<DsBadge>`.
 *
 * Target API: `display, tone, shape`.
 * Legacy API (preserved): `label, color, textColor, outline, variant,
 * transparent, floating, rounded, dot`. The legacy `variant` was
 * `solid|soft|outline`; we keep that surface and translate to DsBadge's
 * `primary|secondary|destructive|outline` (or paint a per-instance colour
 * via CSS-var override when callers pass an explicit `color`).
 */

import { computed } from 'vue'
import DsBadge, { type DsBadgeDisplay, type DsBadgeShape, type DsBadgeTone, type DsBadgeVariant } from '../primitives/Badge/DsBadge.vue'
import { resolveDsColor } from '../../utils/resolveDsColor'

const props = withDefaults(
  defineProps<{
    /** Target display role. Prefer this over raw color tokens. */
    display?: DsBadgeDisplay
    /** Semantic tone. Prefer this over raw color tokens. */
    tone?: DsBadgeTone
    /** Closed shape set. */
    shape?: DsBadgeShape
    /** Badge text (alternative to slot). */
    label?: string
    /** Token name (e.g. `primary`, `success`, `warning`, `error`) or CSS colour. */
    color?: string
    /** Token name (e.g. `white`) or CSS colour. */
    textColor?: string
    /** Visual treatment. */
    variant?: 'solid' | 'soft' | 'outline'
    /** Outline shorthand — equivalent to `variant="outline"`. */
    outline?: boolean
    /** Pill-shaped vs rounded. */
    rounded?: boolean
    /** Tiny dot indicator (no text). */
    dot?: boolean
    /** Render fully transparent (used for floating chip-style overlays). */
    transparent?: boolean
    /** Position the badge absolutely in the top-right corner of its parent. */
    floating?: boolean
  }>(),
  {
    display: 'status',
    color: 'primary',
    textColor: 'white',
    variant: 'solid',
    shape: 'pill',
    outline: false,
    rounded: false,
    dot: false,
    transparent: false,
    floating: false,
  },
)

const effectiveVariant = computed<'solid' | 'soft' | 'outline'>(() =>
  props.outline ? 'outline' : props.variant,
)

/** Map legacy `variant` + `color` to one of DsBadge's four variants. The
 *  per-instance colour is forwarded via CSS-var overrides so any token
 *  resolves through `--ds-color-*`. */
const dsVariant = computed<DsBadgeVariant>(() => {
  if (props.tone && effectiveVariant.value !== 'outline') return 'secondary'
  if (effectiveVariant.value === 'outline') return 'outline'
  if (props.color === 'error' || props.color === 'negative') return 'destructive'
  return 'primary'
})

const overrideStyle = computed(() => {
  if (props.tone) return {}
  const style: Record<string, string> = {
    '--km-badge-color': resolveDsColor(props.color) ?? props.color,
    '--km-badge-text': resolveDsColor(props.textColor) ?? props.textColor,
  }
  return style
})
</script>

<template>
  <DsBadge
    class="km-badge"
    :variant="dsVariant"
    :display="dot ? 'dot' : display"
    :tone="tone"
    :shape="shape"
    :data-km-variant="tone ? undefined : effectiveVariant"
    :data-rounded="rounded ? 'true' : undefined"
    :data-dot="dot ? 'true' : undefined"
    :data-transparent="transparent ? 'true' : undefined"
    :data-floating="floating ? 'true' : undefined"
    :style="overrideStyle"
    data-test="km-badge"
  >
    <template v-if="!dot">
      <slot>{{ label }}</slot>
    </template>
  </DsBadge>
</template>

<style>
/* Solid variant uses the per-instance colour pair so callers can re-skin
 * the badge through `color` / `textColor`. */
.km-badge[data-km-variant='solid'] {
  background: var(--km-badge-color);
  color: var(--km-badge-text);
  border-color: transparent;
}
.km-badge[data-km-variant='soft'] {
  background: color-mix(in srgb, var(--km-badge-color) 16%, transparent);
  color: var(--km-badge-color);
  border-color: transparent;
}
.km-badge[data-km-variant='outline'] {
  background: transparent;
  color: var(--km-badge-color);
  border-color: var(--km-badge-color);
}

.km-badge[data-rounded='true'] { border-radius: var(--ds-radius-full); }
.km-badge[data-transparent='true'] { background: transparent !important; border-color: transparent !important; }

.km-badge[data-dot='true'] {
  inline-size: 8px;
  block-size: 8px;
  padding: 0;
  border-radius: 50%;
}

.km-badge[data-floating='true'] {
  position: absolute;
  inset-block-start: -4px;
  inset-inline-end: -4px;
  z-index: 1;
}
</style>
