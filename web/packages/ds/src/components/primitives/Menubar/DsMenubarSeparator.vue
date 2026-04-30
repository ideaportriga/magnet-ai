<script setup lang="ts">
import type { MenubarSeparatorProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import { MenubarSeparator, useForwardProps } from 'reka-ui'

const props = defineProps<MenubarSeparatorProps>()

const delegatedProps = reactiveOmit(props, 'class' as never)
const forwardedProps = useForwardProps(delegatedProps)
</script>

<template>
  <MenubarSeparator
    class="ds-menu-separator"
    data-test="ds-menubar-separator"
    v-bind="forwardedProps"
  />
</template>
