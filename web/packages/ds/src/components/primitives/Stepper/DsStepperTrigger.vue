<script setup lang="ts">
/**
 * StepperTrigger — clickable element that activates a Stepper step.
 */
import type { StepperTriggerProps } from 'reka-ui'
import { StepperTrigger, useForwardProps } from 'reka-ui'

const props = defineProps<StepperTriggerProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <StepperTrigger
    v-bind="forwarded"
    class="ds-stepper__trigger"
    data-test="ds-stepper-trigger"
  >
    <slot />
  </StepperTrigger>
</template>

<style>
.ds-stepper__trigger {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: var(--ds-space-2xs);
  padding: var(--ds-space-2xs);
  background: transparent;
  border: 0;
  border-radius: var(--ds-radius-md);
  color: inherit;
  cursor: pointer;
  font: inherit;
}
.ds-stepper__trigger:focus-visible {
  outline: 2px solid var(--ds-color-primary);
  outline-offset: 2px;
}
</style>
