<script setup lang="ts">
/**
 * Combobox — searchable select / typeahead. Built on Reka UI's Combobox.
 */
import type { ComboboxRootEmits, ComboboxRootProps } from 'reka-ui'
import { ComboboxRoot, useForwardPropsEmits } from 'reka-ui'

const props = defineProps<ComboboxRootProps>()
const emits = defineEmits<ComboboxRootEmits>()

const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <ComboboxRoot
    v-slot="slotProps"
    v-bind="forwarded"
    data-test="ds-combobox"
  >
    <slot v-bind="slotProps" />
  </ComboboxRoot>
</template>
