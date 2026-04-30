<script setup lang="ts">
import type { MenubarTriggerProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import { MenubarTrigger, useForwardProps } from 'reka-ui'

const props = defineProps<MenubarTriggerProps>()

const delegatedProps = reactiveOmit(props, 'class' as never)
const forwardedProps = useForwardProps(delegatedProps)
</script>

<template>
  <MenubarTrigger
    class="ds-menubar-trigger"
    data-test="ds-menubar-trigger"
    v-bind="forwardedProps"
  >
    <slot />
  </MenubarTrigger>
</template>
