<script setup lang="ts">
import type { DropdownMenuPortalProps } from 'reka-ui'
import { DropdownMenuPortal } from 'reka-ui'

const props = defineProps<DropdownMenuPortalProps>()
</script>

<template>
  <DropdownMenuPortal v-bind="props">
    <slot />
  </DropdownMenuPortal>
</template>
