<script setup lang="ts">
/**
 * SheetTitle — accessible title for the Sheet (announced to screen readers).
 */
import type { DialogTitleProps } from 'reka-ui'
import { DialogTitle } from 'reka-ui'

const props = defineProps<DialogTitleProps>()
</script>

<template>
  <DialogTitle
    v-bind="props"
    class="ds-sheet__title"
    data-test="ds-sheet-title"
  >
    <slot />
  </DialogTitle>
</template>

<style>
.ds-sheet__title {
  color: var(--ds-color-black);
  font-weight: var(--ds-font-weight-semibold);
  line-height: var(--ds-line-height-snug);
}
</style>
