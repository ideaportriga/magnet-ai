<script setup lang="ts">
import { MenubarPortal } from 'reka-ui'

defineProps<{
  to?: string | HTMLElement
  disabled?: boolean
  forceMount?: boolean
}>()
</script>

<template>
  <MenubarPortal :to="to" :disabled="disabled" :force-mount="forceMount">
    <slot />
  </MenubarPortal>
</template>
