<script setup lang="ts">
/**
 * ComboboxTrigger — element that opens the Combobox dropdown when activated.
 */
import type { ComboboxTriggerProps } from 'reka-ui'
import { ComboboxTrigger, useForwardProps } from 'reka-ui'

const props = defineProps<ComboboxTriggerProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <ComboboxTrigger
    v-bind="forwarded"
    class="ds-combobox__trigger"
    data-test="ds-combobox-trigger"
    tabindex="0"
  >
    <slot />
  </ComboboxTrigger>
</template>

<style>
.ds-combobox__trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 0;
  cursor: pointer;
  color: inherit;
}
</style>
