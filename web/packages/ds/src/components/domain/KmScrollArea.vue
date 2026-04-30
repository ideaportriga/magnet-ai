<script setup lang="ts">
/**
 * `<km-scroll-area>` — scrollable region with custom scrollbars. Drop-in
 * over `<DsScrollArea>`.
 *
 * Public API (preserved): `modelValue` (legacy scroll-position API — the
 * value is accepted for compatibility but no longer drives the scroll
 * offset; consumers that need programmatic scrolling should grab the
 * viewport via a ref). The visible scrollbar behaviour is delegated to
 * `<DsScrollArea>` which already exposes `type` and `scrollHideDelay`.
 */

import DsScrollArea from '../primitives/ScrollArea/DsScrollArea.vue'

withDefaults(
  defineProps<{
    /** Legacy scroll-position passthrough (unused — kept for API parity). */
    modelValue?: number | { top?: number; left?: number }
    /** When the scrollbar appears: `hover` (default), `auto`, `always`, `scroll`. */
    type?: 'hover' | 'auto' | 'always' | 'scroll'
    scrollHideDelay?: number
  }>(),
  {
    type: 'hover',
    scrollHideDelay: 600,
  },
)

defineEmits<{
  'update:modelValue': [value: number | { top?: number; left?: number }]
}>()
</script>

<template>
  <DsScrollArea
    class="km-scroll-area"
    :type="type"
    :scroll-hide-delay="scrollHideDelay"
    data-test="km-scroll-area"
  >
    <slot />
  </DsScrollArea>
</template>

<style>
/* Inherits all visuals from .ds-scroll-area. */
</style>
