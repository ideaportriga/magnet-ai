<script setup lang="ts">
import type { ContextMenuSeparatorProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import { ContextMenuSeparator } from 'reka-ui'

const props = defineProps<ContextMenuSeparatorProps>()

const delegatedProps = reactiveOmit(props, 'class' as never)
</script>

<template>
  <ContextMenuSeparator
    class="ds-menu-separator"
    data-test="ds-context-menu-separator"
    v-bind="delegatedProps"
  />
</template>
