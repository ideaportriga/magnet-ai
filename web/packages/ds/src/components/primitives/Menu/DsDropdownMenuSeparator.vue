<script setup lang="ts">
import type { DropdownMenuSeparatorProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import { DropdownMenuSeparator } from 'reka-ui'

const props = defineProps<DropdownMenuSeparatorProps>()

const delegatedProps = reactiveOmit(props, 'class' as never)
</script>

<template>
  <DropdownMenuSeparator
    class="ds-menu-separator"
    data-test="ds-dropdown-menu-separator"
    v-bind="delegatedProps"
  />
</template>
