<script setup lang="ts">
import type { DropdownMenuGroupProps } from 'reka-ui'
import { DropdownMenuGroup, useForwardProps } from 'reka-ui'

const props = defineProps<DropdownMenuGroupProps>()

const forwardedProps = useForwardProps(props)
</script>

<template>
  <DropdownMenuGroup
    data-test="ds-dropdown-menu-group"
    v-bind="forwardedProps"
  >
    <slot />
  </DropdownMenuGroup>
</template>
