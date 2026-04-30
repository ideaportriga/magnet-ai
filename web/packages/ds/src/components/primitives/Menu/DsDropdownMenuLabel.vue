<script setup lang="ts">
import type { DropdownMenuLabelProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import { DropdownMenuLabel, useForwardProps } from 'reka-ui'

const props = defineProps<DropdownMenuLabelProps & { inset?: boolean }>()

const delegatedProps = reactiveOmit(props, 'class' as never, 'inset' as never)
const forwardedProps = useForwardProps(delegatedProps)
</script>

<template>
  <DropdownMenuLabel
    class="ds-menu-label"
    data-test="ds-dropdown-menu-label"
    :data-inset="inset ? '' : undefined"
    v-bind="forwardedProps"
  >
    <slot />
  </DropdownMenuLabel>
</template>
