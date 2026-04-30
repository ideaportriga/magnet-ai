<script setup lang="ts">
/**
 * StepperSeparator — line connecting consecutive Stepper items.
 */
import type { StepperSeparatorProps } from 'reka-ui'
import { StepperSeparator, useForwardProps } from 'reka-ui'

const props = defineProps<StepperSeparatorProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <StepperSeparator
    v-bind="forwarded"
    class="ds-stepper__separator"
    data-test="ds-stepper-separator"
  />
</template>

<style>
.ds-stepper__separator {
  background: var(--ds-color-border);
}
.ds-stepper__item[data-disabled] .ds-stepper__separator {
  background: var(--ds-color-border);
  opacity: 0.5;
}
.ds-stepper__item[data-state='completed'] .ds-stepper__separator {
  background: var(--ds-color-accent);
}
</style>
