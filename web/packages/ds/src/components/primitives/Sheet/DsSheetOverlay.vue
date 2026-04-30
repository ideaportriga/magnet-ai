<script setup lang="ts">
/**
 * SheetOverlay — semi-transparent backdrop behind a Sheet. Animates in/out
 * via the [data-state] attribute managed by Reka UI.
 */
import type { DialogOverlayProps } from 'reka-ui'
import { DialogOverlay } from 'reka-ui'

const props = defineProps<DialogOverlayProps>()
</script>

<template>
  <DialogOverlay
    v-bind="props"
    class="ds-sheet__overlay"
    data-test="ds-sheet-overlay"
  >
    <slot />
  </DialogOverlay>
</template>

<style>
.ds-sheet__overlay {
  position: fixed;
  inset: 0;
  z-index: var(--ds-z-modal);
  background: rgba(15, 16, 26, 0.55);
  animation: ds-fade-in var(--ds-duration-base) var(--ds-ease-out);
}
.ds-sheet__overlay[data-state='closed'] {
  animation: ds-fade-out var(--ds-duration-fast) var(--ds-ease-in);
}
</style>
