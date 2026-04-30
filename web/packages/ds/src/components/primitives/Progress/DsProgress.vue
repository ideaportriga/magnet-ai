<script setup lang="ts">
/**
 * Progress — linear progress bar with determinate / indeterminate modes.
 * Replaces Quasar's `<km-linear-progress>` and `q-circular-progress` (linear
 * only — for circular, use a small SVG component).
 *
 *   <DsProgress :value="60" />            // determinate, 60%
 *   <DsProgress />                        // indeterminate
 */

import { ProgressIndicator, ProgressRoot } from 'reka-ui'
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    /** 0..100. Pass `null` (or omit) for indeterminate. */
    value?: number | null
    /** Visual size. */
    size?: 'sm' | 'md' | 'lg'
    /** Tone — primary by default; semantic for status bars. */
    tone?: 'primary' | 'success' | 'warning' | 'error'
  }>(),
  {
    size: 'md',
    tone: 'primary',
  },
)

const max = 100
const isIndeterminate = computed(() => props.value == null || Number.isNaN(props.value))
</script>

<template>
  <ProgressRoot
    :model-value="isIndeterminate ? null : Math.min(max, Math.max(0, value as number))"
    :max="max"
    class="ds-progress"
    :data-size="size"
    :data-tone="tone"
    :data-state="isIndeterminate ? 'indeterminate' : 'determinate'"
    data-test="ds-progress"
  >
    <ProgressIndicator
      class="ds-progress__indicator"
      :style="!isIndeterminate ? { width: `${value}%` } : undefined"
    />
  </ProgressRoot>
</template>

<style>
.ds-progress {
  position: relative;
  inline-size: 100%;
  block-size: 6px;
  background: var(--ds-color-border);
  border-radius: var(--ds-radius-full);
  overflow: hidden;
}
.ds-progress[data-size='sm'] { block-size: 4px; }
.ds-progress[data-size='lg'] { block-size: 10px; }

.ds-progress__indicator {
  block-size: 100%;
  background: var(--ds-color-primary);
  border-radius: inherit;
  transition: width var(--ds-duration-base) var(--ds-ease-out);
}

.ds-progress[data-tone='success'] .ds-progress__indicator { background: var(--ds-color-success-text); }
.ds-progress[data-tone='warning'] .ds-progress__indicator { background: var(--ds-color-warning-secondary); }
.ds-progress[data-tone='error']   .ds-progress__indicator { background: var(--ds-color-error); }

.ds-progress[data-state='indeterminate'] .ds-progress__indicator {
  inline-size: 30%;
  animation: ds-progress-indeterminate 1.4s var(--ds-ease-in-out) infinite;
}

@keyframes ds-progress-indeterminate {
  0%   { transform: translateX(-100%); }
  100% { transform: translateX(400%); }
}
</style>
