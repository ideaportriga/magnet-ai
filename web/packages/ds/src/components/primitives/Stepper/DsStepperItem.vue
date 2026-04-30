<script setup lang="ts">
/**
 * StepperItem — represents one step in the Stepper sequence. Carries the
 * `[data-state]` (active/inactive/completed) and `[data-disabled]` attrs
 * that descendant indicator/separator/title/description style off of.
 */
import type { StepperItemProps } from 'reka-ui'
import { StepperItem, useForwardProps } from 'reka-ui'

const props = defineProps<StepperItemProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <StepperItem
    v-slot="slotProps"
    v-bind="forwarded"
    class="ds-stepper__item"
    data-test="ds-stepper-item"
  >
    <slot v-bind="slotProps" />
  </StepperItem>
</template>

<style>
.ds-stepper__item {
  display: flex;
  align-items: center;
  gap: var(--ds-space-xs);
}
.ds-stepper__item[data-disabled] {
  pointer-events: none;
}
</style>
