<script setup lang="ts">
import type { MenubarItemEmits, MenubarItemProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import {
  MenubarItem,
  useForwardPropsEmits,
} from 'reka-ui'

const props = withDefaults(
  defineProps<MenubarItemProps & {
    inset?: boolean
    variant?: 'default' | 'destructive'
  }>(),
  { variant: 'default' },
)
const emits = defineEmits<MenubarItemEmits>()

const delegatedProps = reactiveOmit(props, 'class' as never, 'inset' as never, 'variant' as never)
const forwarded = useForwardPropsEmits(delegatedProps, emits)
</script>

<template>
  <MenubarItem
    class="ds-menu-item"
    data-test="ds-menubar-item"
    :data-inset="inset ? '' : undefined"
    :data-variant="variant"
    v-bind="forwarded"
  >
    <slot />
  </MenubarItem>
</template>
