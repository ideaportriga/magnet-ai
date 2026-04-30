<script setup lang="ts">
/**
 * `<km-loader>` — circular spinner (drop-in for the legacy three-body
 * loader). All loaders in the app render the same circle now; the legacy
 * `name="three-body"` prop is accepted but ignored so existing call-sites
 * keep working without churn.
 *
 * Sizing / speed / colour are wired to CSS custom properties so the markup
 * stays a single block. New code should prefer `<DsSpinner>` directly.
 */

import { computed } from 'vue'
import { resolveDsColor } from '../../utils/resolveDsColor'

type LoaderSizePreset = 'xs' | 'sm' | 'md' | 'lg' | 'xl'

const SIZE_PRESETS: Record<LoaderSizePreset, string> = {
  xs: 'var(--ds-loader-size-xs)',
  sm: 'var(--ds-loader-size-sm)',
  md: 'var(--ds-loader-size-md)',
  lg: 'var(--ds-loader-size-lg)',
  xl: 'var(--ds-loader-size-xl)',
}

const props = withDefaults(
  defineProps<{
    /** Accepted for legacy parity; ignored — every variant renders the
     *  same circular spinner. */
    name?: string
    /** Size preset (`xs|sm|md|lg|xl` resolves to a token) or a CSS length.
     *  New call-sites should prefer presets so the scale stays consistent. */
    size?: string
    speed?: string
    /** Token name (e.g. 'primary', 'icon') or any CSS colour. */
    color?: string
  }>(),
  {
    name: 'three-body',
    size: '32px',
    speed: '0.7s',
    color: 'primary',
  },
)

function resolveSize(value: string): string {
  if (value in SIZE_PRESETS) return SIZE_PRESETS[value as LoaderSizePreset]
  return value
}

const cssVars = computed(() => {
  const colourValue = /^[a-z][a-z0-9-]*$/i.test(props.color)
    ? resolveDsColor(props.color)
    : props.color
  return {
    '--km-loader-size': resolveSize(props.size),
    '--km-loader-speed': props.speed,
    '--km-loader-color': colourValue ?? props.color,
  } as Record<string, string>
})
</script>

<template>
  <span
    class="km-loader"
    role="status"
    aria-label="Loading"
    :style="cssVars"
    data-test="km-loader"
  />
</template>

<style>
.km-loader {
  display: inline-block;
  inline-size: var(--km-loader-size);
  block-size: var(--km-loader-size);
  border: 2px solid var(--km-loader-color);
  border-block-end-color: transparent;
  border-radius: 50%;
  animation: ds-spin var(--km-loader-speed) var(--ds-ease-linear) infinite;
  flex: none;
}

@media (prefers-reduced-motion: reduce) {
  .km-loader { animation-duration: 2s; }
}
</style>
