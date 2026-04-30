<script setup lang="ts">
import type { DrawerCloseProps } from 'vaul-vue'
import { DrawerClose } from 'vaul-vue'

const props = defineProps<DrawerCloseProps>()
</script>

<template>
  <DrawerClose
    data-test="ds-drawer-close"
    v-bind="props"
  >
    <slot />
  </DrawerClose>
</template>
