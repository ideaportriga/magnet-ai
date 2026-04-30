<script setup lang="ts">
/**
 * `<km-slider-card>` — labelled slider with inline numeric input, min/max
 * captions, optional info tooltip and a "revert to default" button.
 *
 * Drop-in for the legacy SliderCard.
 */

import { computed, ref } from 'vue'
import KmBtn from './KmBtn.vue'
import KmGlyph from './KmGlyph.vue'
import KmInputFlat from './KmInputFlat.vue'
import KmSlider from './KmSlider.vue'
import KmTooltip from './KmTooltip.vue'

const props = withDefaults(
  defineProps<{
    modelValue?: number
    defaultValue?: number
    name?: string
    description?: string
    minLabel?: string
    maxLabel?: string
    infoTooltip?: string
    min?: number
    max?: number
    step?: number
  }>(),
  {
    modelValue: 0,
    defaultValue: 0.5,
    name: 'Threshold',
    description: '',
    minLabel: 'Minimum',
    maxLabel: 'Maximum',
    infoTooltip: '',
    min: 0,
    max: 1,
    step: 0.01,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: number]
}>()

const hover = ref(false)

const inputNumber = computed({
  get: () => (props.modelValue != null ? String(props.modelValue) : ''),
  set: (next: string) => {
    const numeric = Number.parseFloat(next)
    if (Number.isNaN(numeric)) {
      emit('update:modelValue', 0)
      return
    }
    if (numeric > props.max) emit('update:modelValue', props.max)
    else if (numeric < props.min) emit('update:modelValue', props.min)
    else emit('update:modelValue', numeric)
  },
})
</script>

<template>
  <div
    class="km-slider-card stack"
    data-gap="2xs"
    data-test="km-slider-card"
    @mouseover="hover = true"
    @mouseleave="hover = false"
  >
    <div class="cluster" data-justify="between" data-align="center">
      <div class="cluster gap-xs" data-align="center">
        <span class="km-slider-card__name">{{ name }}</span>
        <KmTooltip v-if="infoTooltip" :label="infoTooltip">
          <template #trigger>
            <KmGlyph name="info" size="20px" />
          </template>
        </KmTooltip>
      </div>
      <span class="km-slider-card__value" :class="{ 'bg-light': hover }">
        <KmInputFlat v-model="inputNumber" />
      </span>
    </div>

    <div class="cluster gap-sm" data-align="center">
      <span class="grow">
        <KmSlider
          :model-value="modelValue"
          :min="min"
          :max="max"
          :step="step"
          @update:model-value="emit('update:modelValue', $event)"
        />
      </span>
      <KmBtn
        flat
        simple
        icon="refresh"
        :tooltip="`Revert to ${defaultValue}`"
        @click="emit('update:modelValue', defaultValue)"
      />
    </div>

    <div class="cluster" data-justify="between">
      <span class="km-slider-card__caption">{{ minLabel }}</span>
      <span class="km-slider-card__caption">{{ maxLabel }}</span>
    </div>

    <p v-if="description" class="km-slider-card__description">{{ description }}</p>
  </div>
</template>

<style>
.km-slider-card { padding: var(--ds-space-sm) 0; }
.km-slider-card__name { font-weight: var(--ds-font-weight-medium); }
.km-slider-card__value { display: inline-flex; min-inline-size: 50px; justify-content: flex-end; }
.km-slider-card__caption { font-size: var(--ds-font-size-caption); color: var(--ds-color-text-grey); }
.km-slider-card__description { font-size: var(--ds-font-size-caption); color: var(--ds-color-text-grey); margin: 0; }
</style>
