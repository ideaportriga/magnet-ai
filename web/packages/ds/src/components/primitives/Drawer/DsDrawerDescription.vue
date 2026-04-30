<script setup lang="ts">
import type { DrawerDescriptionProps } from 'vaul-vue'
import { DrawerDescription } from 'vaul-vue'

const props = defineProps<DrawerDescriptionProps>()
</script>

<template>
  <DrawerDescription
    class="ds-drawer__description"
    data-test="ds-drawer-description"
    v-bind="props"
  >
    <slot />
  </DrawerDescription>
</template>

<style>
.ds-drawer__description {
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-text-grey);
  margin: 0;
}
</style>
