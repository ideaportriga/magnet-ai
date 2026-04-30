<script setup lang="ts">
/**
 * StepperTitle — short heading for a step.
 */
import type { StepperTitleProps } from 'reka-ui'
import { StepperTitle, useForwardProps } from 'reka-ui'

const props = defineProps<StepperTitleProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <StepperTitle
    v-bind="forwarded"
    class="ds-stepper__title"
    data-test="ds-stepper-title"
  >
    <slot />
  </StepperTitle>
</template>

<style>
.ds-stepper__title {
  font-size: var(--ds-font-size-body);
  font-weight: var(--ds-font-weight-semibold);
  white-space: nowrap;
}
</style>
