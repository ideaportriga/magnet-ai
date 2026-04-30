<script setup lang="ts">
import type { MenubarLabelProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import { MenubarLabel } from 'reka-ui'

const props = defineProps<MenubarLabelProps & { inset?: boolean }>()
const delegatedProps = reactiveOmit(props, 'class' as never, 'inset' as never)
</script>

<template>
  <MenubarLabel
    class="ds-menu-label"
    data-test="ds-menubar-label"
    :data-inset="inset ? '' : undefined"
    v-bind="delegatedProps"
  >
    <slot />
  </MenubarLabel>
</template>
