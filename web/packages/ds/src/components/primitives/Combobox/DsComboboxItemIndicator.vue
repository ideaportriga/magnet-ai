<script setup lang="ts">
/**
 * ComboboxItemIndicator — only visible when its parent ComboboxItem is
 * the selected one. Right-aligned by default (e.g. for a checkmark).
 */
import type { ComboboxItemIndicatorProps } from 'reka-ui'
import { ComboboxItemIndicator, useForwardProps } from 'reka-ui'

const props = defineProps<ComboboxItemIndicatorProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <ComboboxItemIndicator
    v-bind="forwarded"
    class="ds-combobox__item-indicator"
    data-test="ds-combobox-item-indicator"
  >
    <slot />
  </ComboboxItemIndicator>
</template>

<style>
.ds-combobox__item-indicator {
  margin-inline-start: auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>
