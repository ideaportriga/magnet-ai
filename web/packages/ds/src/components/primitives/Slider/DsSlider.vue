<script setup lang="ts">
/**
 * Slider — single-thumb numeric slider. For range sliders, pass an array via
 * v-model and Reka renders a thumb per value.
 *
 *   <DsSlider v-model="volume" :min="0" :max="100" :step="5" />
 *   <DsSlider v-model="range" :min="0" :max="100" />  // [low, high]
 */

import { SliderRange, SliderRoot, SliderThumb, SliderTrack } from 'reka-ui'

withDefaults(
  defineProps<{
    modelValue?: number | number[]
    min?: number
    max?: number
    step?: number
    disabled?: boolean
    orientation?: 'horizontal' | 'vertical'
  }>(),
  {
    min: 0,
    max: 100,
    step: 1,
    orientation: 'horizontal',
  },
)

defineEmits<{
  'update:modelValue': [value: number[]]
}>()
</script>

<template>
  <SliderRoot
    :model-value="Array.isArray(modelValue) ? modelValue : [modelValue ?? 0]"
    :min="min"
    :max="max"
    :step="step"
    :disabled="disabled"
    :orientation="orientation"
    class="ds-slider"
    :data-orientation="orientation"
    data-test="ds-slider"
    @update:model-value="$emit('update:modelValue', $event as number[])"
  >
    <SliderTrack class="ds-slider__track">
      <SliderRange class="ds-slider__range" />
    </SliderTrack>
    <SliderThumb
      v-for="(_, idx) in Array.isArray(modelValue) ? modelValue : [0]"
      :key="idx"
      class="ds-slider__thumb"
      :aria-label="`Slider value ${idx + 1}`"
    />
  </SliderRoot>
</template>

<style>
.ds-slider {
  position: relative;
  display: flex;
  align-items: center;
  user-select: none;
  touch-action: none;
}
.ds-slider[data-orientation='horizontal'] {
  inline-size: 100%;
  block-size: 20px;
}
.ds-slider[data-orientation='vertical'] {
  flex-direction: column;
  block-size: 100%;
  inline-size: 20px;
}

.ds-slider__track {
  position: relative;
  flex-grow: 1;
  border-radius: var(--ds-radius-full);
  background: var(--ds-color-border);
}
.ds-slider[data-orientation='horizontal'] .ds-slider__track { block-size: 4px; }
.ds-slider[data-orientation='vertical']   .ds-slider__track { inline-size: 4px; }

.ds-slider__range {
  position: absolute;
  background: var(--ds-color-primary);
  border-radius: var(--ds-radius-full);
}
.ds-slider[data-orientation='horizontal'] .ds-slider__range { block-size: 100%; }
.ds-slider[data-orientation='vertical']   .ds-slider__range { inline-size: 100%; }

.ds-slider__thumb {
  display: block;
  inline-size: 16px;
  block-size: 16px;
  background: var(--ds-color-white);
  border: 2px solid var(--ds-color-primary);
  border-radius: 50%;
  box-shadow: var(--ds-shadow-sm);
  transition: transform var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-slider__thumb:hover { transform: scale(1.1); }
.ds-slider__thumb:focus-visible {
  outline: 2px solid var(--ds-color-primary);
  outline-offset: 2px;
}
</style>
