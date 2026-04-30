<script setup lang="ts">
/**
 * SheetDescription — accessible descriptive text linked to the Sheet.
 */
import type { DialogDescriptionProps } from 'reka-ui'
import { DialogDescription } from 'reka-ui'

const props = defineProps<DialogDescriptionProps>()
</script>

<template>
  <DialogDescription
    v-bind="props"
    class="ds-sheet__description"
    data-test="ds-sheet-description"
  >
    <slot />
  </DialogDescription>
</template>

<style>
.ds-sheet__description {
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-text-grey);
}
</style>
