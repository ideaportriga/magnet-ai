<script setup lang="ts">
/**
 * StepperDescription — secondary text under a step title.
 */
import type { StepperDescriptionProps } from 'reka-ui'
import { StepperDescription, useForwardProps } from 'reka-ui'

const props = defineProps<StepperDescriptionProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <StepperDescription
    v-slot="slotProps"
    v-bind="forwarded"
    class="ds-stepper__description"
    data-test="ds-stepper-description"
  >
    <slot v-bind="slotProps" />
  </StepperDescription>
</template>

<style>
.ds-stepper__description {
  font-size: var(--ds-font-size-xs);
  color: var(--ds-color-text-grey);
}
</style>
