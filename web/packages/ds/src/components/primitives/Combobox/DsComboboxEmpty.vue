<script setup lang="ts">
/**
 * ComboboxEmpty — message rendered when no items match the current search.
 */
import type { ComboboxEmptyProps } from 'reka-ui'
import { ComboboxEmpty } from 'reka-ui'

const props = defineProps<ComboboxEmptyProps>()
</script>

<template>
  <ComboboxEmpty
    v-bind="props"
    class="ds-combobox__empty"
    data-test="ds-combobox-empty"
  >
    <slot />
  </ComboboxEmpty>
</template>

<style>
.ds-combobox__empty {
  padding-block: var(--ds-space-xl);
  text-align: center;
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-text-grey);
}
</style>
