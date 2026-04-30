<script setup lang="ts">
/**
 * NumberField — accessible number input with increment/decrement controls.
 * Built on Reka UI's NumberField.
 */
import type { NumberFieldRootEmits, NumberFieldRootProps } from 'reka-ui'
import { NumberFieldRoot, useForwardPropsEmits } from 'reka-ui'

const props = defineProps<NumberFieldRootProps>()
const emits = defineEmits<NumberFieldRootEmits>()

const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <NumberFieldRoot
    v-slot="slotProps"
    v-bind="forwarded"
    class="ds-number-field"
    data-test="ds-number-field"
  >
    <slot v-bind="slotProps" />
  </NumberFieldRoot>
</template>

<style>
.ds-number-field {
  display: grid;
  gap: var(--ds-space-xs);
}
</style>
