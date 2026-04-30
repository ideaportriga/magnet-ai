<script setup lang="ts">
/**
 * `<km-linear-progress>` — horizontal progress bar. Drop-in over
 * `<DsProgress>`. The legacy contract took `value` as a 0..1 fraction;
 * `DsProgress` works in 0..100, so we scale at the boundary. `color` and
 * `trackColor` are forwarded as CSS-var overrides; `dark` paints over
 * darker surfaces.
 *
 * Public API (preserved): `value, color, trackColor, indeterminate, dark,
 * size`.
 */

import { computed } from 'vue'
import DsProgress from '../primitives/Progress/DsProgress.vue'
import { resolveDsColor } from '../../utils/resolveDsColor'

const props = withDefaults(
  defineProps<{
    /** 0..1 fraction (legacy). */
    value?: number
    /** When true, animate an indeterminate stripe instead. */
    indeterminate?: boolean
    /** Token name (e.g. `primary`, `success`) or any CSS colour. */
    color?: string
    /** Track colour (token or CSS colour). */
    trackColor?: string
    /** Hint that the bar is rendered on a dark surface. */
    dark?: boolean
    /** Height: legacy CSS length (e.g. `4px`) or Ds preset. */
    size?: string
  }>(),
  {
    value: 0,
    indeterminate: false,
    color: '',
    trackColor: '',
    dark: false,
    size: '4px',
  },
)

const dsValue = computed<number | null>(() => {
  if (props.indeterminate) return null
  return Math.round(Math.min(Math.max(props.value, 0), 1) * 100)
})

/** Map legacy CSS-length size → Ds preset. */
const dsSize = computed<'sm' | 'md' | 'lg'>(() => {
  const s = props.size
  if (s === 'sm' || s === '2px' || s === '3px' || s === '4px') return 'sm'
  if (s === 'lg' || s === '8px' || s === '10px' || s === '12px') return 'lg'
  return 'md'
})

const overrideStyle = computed(() => {
  const style: Record<string, string> = {}
  if (props.color) {
    style['--ds-color-primary'] = resolveDsColor(props.color) ?? props.color
  }
  if (props.trackColor) {
    style['--ds-color-border'] = resolveDsColor(props.trackColor) ?? props.trackColor
  } else if (props.dark) {
    style['--ds-color-border'] = 'rgba(255, 255, 255, 0.18)'
  }
  return style
})
</script>

<template>
  <DsProgress
    class="km-linear-progress"
    :value="dsValue"
    :size="dsSize"
    :style="overrideStyle"
    :data-dark="dark ? 'true' : undefined"
    data-test="km-linear-progress"
  />
</template>

<style>
/* Inherits .ds-progress visuals; the CSS-var overrides above re-skin the
 * indicator and the track per-instance. */
</style>
