<script setup lang="ts">
/**
 * `<km-slider>` — single-thumb numeric slider. Drop-in over `<DsSlider>`.
 *
 * Public API (preserved): `modelValue, min, max, step, disable, label,
 * vertical`. We unwrap `[number]` ⇆ `number` so callers stay scalar, and
 * map the legacy `disable` boolean to `disabled`.
 */

import { computed } from 'vue'
import DsSlider from '../primitives/Slider/DsSlider.vue'

const props = withDefaults(
  defineProps<{
    modelValue?: number
    min?: number
    max?: number
    step?: number
    /** Legacy disabled flag. */
    disable?: boolean
    /** Modern disabled flag (alias). */
    disabled?: boolean
    /** Visible label rendered above the track. */
    label?: string
    /** Render the slider vertically. */
    vertical?: boolean
  }>(),
  {
    modelValue: 0,
    min: 0,
    max: 1,
    step: 0.01,
    disable: false,
    disabled: false,
    label: '',
    vertical: false,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: number]
}>()

const isDisabled = computed(() => props.disable || props.disabled)
const orientation = computed<'horizontal' | 'vertical'>(() =>
  props.vertical ? 'vertical' : 'horizontal',
)

function onUpdate(value: number[]) {
  if (value.length) emit('update:modelValue', value[0]!)
}
</script>

<template>
  <span class="km-slider" :data-orientation="orientation">
    <span v-if="label" class="km-slider__label">{{ label }}</span>
    <DsSlider
      class="km-slider__control"
      :model-value="[modelValue]"
      :min="min"
      :max="max"
      :step="step"
      :disabled="isDisabled"
      :orientation="orientation"
      data-test="km-slider"
      @update:model-value="onUpdate"
    />
  </span>
</template>

<style>
.km-slider {
  display: inline-flex;
  flex-direction: column;
  gap: var(--ds-space-xs);
  inline-size: 100%;
}
.km-slider[data-orientation='vertical'] {
  flex-direction: row;
  align-items: center;
  inline-size: auto;
  block-size: 100%;
}
.km-slider__label {
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-secondary-text);
}
.km-slider__control { flex: 1 1 auto; }
</style>
