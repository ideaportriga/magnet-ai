<script setup lang="ts">
/**
 * `<km-score>` — colour-coded numeric score chip. Drop-in for the legacy.
 *
 *   ≥ 4 → success palette
 *   3..4 or 'Not rated' → in-progress palette
 *   < 3 → error palette
 */

import { computed } from 'vue'

const props = defineProps<{
  score: number | string | null | undefined
}>()

const isRated = computed(() => typeof props.score === 'number')

const tone = computed<'success' | 'neutral' | 'error'>(() => {
  if (!isRated.value) return 'neutral'
  const value = props.score as number
  if (value > 4) return 'success'
  if (value >= 3) return 'neutral'
  return 'error'
})

const label = computed(() => {
  if (!isRated.value) return 'Not rated'
  return (props.score as number).toFixed(2)
})
</script>

<template>
  <span class="km-score" :data-tone="tone" data-test="km-score">
    {{ label }}
  </span>
</template>

<style>
.km-score {
  display: inline-flex;
  align-items: center;
  padding: 2px var(--ds-space-sm);
  border-radius: var(--ds-radius-full);
  font-size: var(--ds-font-size-caption);
  font-weight: var(--ds-font-weight-medium);
}
.km-score[data-tone='success'] {
  background: var(--ds-color-status-ready);
  color: var(--ds-color-status-ready-text);
}
.km-score[data-tone='neutral'] {
  background: var(--ds-color-in-progress);
  color: var(--ds-color-text-grey);
}
.km-score[data-tone='error'] {
  background: var(--ds-color-error-bg);
  color: var(--ds-color-error-text);
}
</style>
