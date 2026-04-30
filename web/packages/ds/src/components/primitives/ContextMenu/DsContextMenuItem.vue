<script setup lang="ts">
import type { ContextMenuItemEmits, ContextMenuItemProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import {
  ContextMenuItem,
  useForwardPropsEmits,
} from 'reka-ui'

const props = withDefaults(
  defineProps<ContextMenuItemProps & {
    inset?: boolean
    variant?: 'default' | 'destructive'
  }>(),
  { variant: 'default' },
)
const emits = defineEmits<ContextMenuItemEmits>()

const delegatedProps = reactiveOmit(props, 'inset' as never, 'variant' as never)
const forwarded = useForwardPropsEmits(delegatedProps, emits)
</script>

<template>
  <ContextMenuItem
    class="ds-menu-item"
    data-test="ds-context-menu-item"
    :data-inset="inset ? '' : undefined"
    :data-variant="variant"
    v-bind="forwarded"
  >
    <slot />
  </ContextMenuItem>
</template>
