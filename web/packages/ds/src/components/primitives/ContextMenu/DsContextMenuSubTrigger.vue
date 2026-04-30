<script setup lang="ts">
import type { ContextMenuSubTriggerProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import {
  ContextMenuSubTrigger,
  useForwardProps,
} from 'reka-ui'

const props = defineProps<ContextMenuSubTriggerProps & { inset?: boolean }>()

const delegatedProps = reactiveOmit(props, 'class' as never, 'inset' as never)
const forwardedProps = useForwardProps(delegatedProps)
</script>

<template>
  <ContextMenuSubTrigger
    class="ds-menu-item"
    data-test="ds-context-menu-sub-trigger"
    :data-inset="inset ? '' : undefined"
    v-bind="forwardedProps"
  >
    <slot />
    <svg
      class="ds-menu-sub-trigger__chevron"
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
    >
      <polyline points="9 18 15 12 9 6" />
    </svg>
  </ContextMenuSubTrigger>
</template>
