<script setup lang="ts">
/**
 * Stepper — multi-step progress / wizard. Built on Reka UI's Stepper.
 */
import type { StepperRootEmits, StepperRootProps } from 'reka-ui'
import { StepperRoot, useForwardPropsEmits } from 'reka-ui'

const props = defineProps<StepperRootProps>()
const emits = defineEmits<StepperRootEmits>()

const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <StepperRoot
    v-slot="slotProps"
    v-bind="forwarded"
    class="ds-stepper"
    data-test="ds-stepper"
  >
    <slot v-bind="slotProps" />
  </StepperRoot>
</template>

<style>
.ds-stepper {
  display: flex;
  gap: var(--ds-space-xs);
}
.ds-stepper[data-orientation='vertical'] {
  flex-direction: column;
}
</style>
