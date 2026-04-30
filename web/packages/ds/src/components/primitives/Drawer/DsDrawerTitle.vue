<script setup lang="ts">
import type { DrawerTitleProps } from 'vaul-vue'
import { DrawerTitle } from 'vaul-vue'

const props = defineProps<DrawerTitleProps>()
</script>

<template>
  <DrawerTitle
    class="ds-drawer__title"
    data-test="ds-drawer-title"
    v-bind="props"
  >
    <slot />
  </DrawerTitle>
</template>

<style>
.ds-drawer__title {
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-h2);
  font-weight: var(--ds-font-weight-semibold);
  line-height: var(--ds-line-height-snug);
  color: var(--ds-color-black);
  margin: 0;
}
</style>
