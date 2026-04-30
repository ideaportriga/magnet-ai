<script setup lang="ts">
/**
 * ComboboxGroup — labelled group of ComboboxItem children.
 */
import type { ComboboxGroupProps } from 'reka-ui'
import { ComboboxGroup, ComboboxLabel } from 'reka-ui'

const props = defineProps<ComboboxGroupProps & { heading?: string }>()
</script>

<template>
  <ComboboxGroup
    v-bind="props"
    class="ds-combobox__group"
    data-test="ds-combobox-group"
  >
    <ComboboxLabel v-if="heading" class="ds-combobox__group-heading">
      {{ heading }}
    </ComboboxLabel>
    <slot />
  </ComboboxGroup>
</template>

<style>
.ds-combobox__group {
  overflow: hidden;
  padding: var(--ds-space-2xs);
  color: var(--ds-color-black);
}
.ds-combobox__group-heading {
  display: block;
  padding-inline: var(--ds-space-xs);
  padding-block: var(--ds-space-2xs);
  font-size: var(--ds-font-size-xs);
  font-weight: var(--ds-font-weight-medium);
  color: var(--ds-color-text-grey);
}
</style>
