<script setup lang="ts">
/**
 * ComboboxSeparator — divider between Combobox groups / sections.
 */
import type { ComboboxSeparatorProps } from 'reka-ui'
import { ComboboxSeparator } from 'reka-ui'

const props = defineProps<ComboboxSeparatorProps>()
</script>

<template>
  <ComboboxSeparator
    v-bind="props"
    class="ds-combobox__separator"
    data-test="ds-combobox-separator"
  >
    <slot />
  </ComboboxSeparator>
</template>

<style>
.ds-combobox__separator {
  block-size: 1px;
  margin-inline: calc(-1 * var(--ds-space-2xs));
  background: var(--ds-color-border);
}
</style>
