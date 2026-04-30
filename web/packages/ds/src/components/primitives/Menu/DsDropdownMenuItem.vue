<script setup lang="ts">
import type { DropdownMenuItemEmits, DropdownMenuItemProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import {
  DropdownMenuItem,
  useForwardPropsEmits,
} from 'reka-ui'

const props = withDefaults(
  defineProps<DropdownMenuItemProps & {
    inset?: boolean
    variant?: 'default' | 'destructive'
  }>(),
  { variant: 'default' },
)
const emits = defineEmits<DropdownMenuItemEmits>()

const delegatedProps = reactiveOmit(props, 'inset' as never, 'variant' as never)
const forwarded = useForwardPropsEmits(delegatedProps, emits)
</script>

<template>
  <DropdownMenuItem
    class="ds-menu-item"
    data-test="ds-dropdown-menu-item"
    :data-inset="inset ? '' : undefined"
    :data-variant="variant"
    v-bind="forwarded"
  >
    <slot />
  </DropdownMenuItem>
</template>
