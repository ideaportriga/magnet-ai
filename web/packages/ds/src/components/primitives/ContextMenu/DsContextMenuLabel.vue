<script setup lang="ts">
import type { ContextMenuLabelProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import { ContextMenuLabel } from 'reka-ui'

const props = defineProps<ContextMenuLabelProps & { inset?: boolean }>()

const delegatedProps = reactiveOmit(props, 'class' as never, 'inset' as never)
</script>

<template>
  <ContextMenuLabel
    class="ds-menu-label"
    data-test="ds-context-menu-label"
    :data-inset="inset ? '' : undefined"
    v-bind="delegatedProps"
  >
    <slot />
  </ContextMenuLabel>
</template>
