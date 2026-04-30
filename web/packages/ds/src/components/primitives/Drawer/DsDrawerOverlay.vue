<script setup lang="ts">
import type { DialogOverlayProps } from 'reka-ui'
import { DrawerOverlay } from 'vaul-vue'

const props = defineProps<DialogOverlayProps>()
</script>

<template>
  <DrawerOverlay
    class="ds-drawer__overlay"
    data-test="ds-drawer-overlay"
    v-bind="props"
  />
</template>

<style>
.ds-drawer__overlay {
  position: fixed;
  inset: 0;
  z-index: var(--ds-z-modal);
  background: rgba(15, 16, 26, 0.45);
  animation: ds-fade-in var(--ds-duration-base) var(--ds-ease-out);
}
.ds-drawer__overlay[data-state='closed'] {
  animation: ds-fade-out var(--ds-duration-fast) var(--ds-ease-in);
}
</style>
