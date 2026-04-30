<script setup lang="ts">
/**
 * StepperIndicator — circular badge showing the step number / icon. Inherits
 * its color treatment from the parent StepperItem's [data-state].
 */
import type { StepperIndicatorProps } from 'reka-ui'
import { StepperIndicator, useForwardProps } from 'reka-ui'

const props = defineProps<StepperIndicatorProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <StepperIndicator
    v-slot="slotProps"
    v-bind="forwarded"
    class="ds-stepper__indicator"
    data-test="ds-stepper-indicator"
  >
    <slot v-bind="slotProps" />
  </StepperIndicator>
</template>

<style>
.ds-stepper__indicator {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  inline-size: 32px;
  block-size: 32px;
  border-radius: var(--ds-radius-full);
  color: var(--ds-color-text-grey);
  background: transparent;
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
}
.ds-stepper__item[data-disabled] .ds-stepper__indicator {
  opacity: 0.5;
}
.ds-stepper__item[data-state='active'] .ds-stepper__indicator {
  background: var(--ds-color-primary);
  color: var(--ds-color-btn-primary-text);
}
.ds-stepper__item[data-state='completed'] .ds-stepper__indicator {
  background: var(--ds-color-accent-bg);
  color: var(--ds-color-accent);
}
</style>
