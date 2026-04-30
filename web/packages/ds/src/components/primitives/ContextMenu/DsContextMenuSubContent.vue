<script setup lang="ts">
import type { ContextMenuSubContentEmits, ContextMenuSubContentProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import {
  ContextMenuSubContent,
  useForwardPropsEmits,
} from 'reka-ui'

const props = defineProps<ContextMenuSubContentProps>()
const emits = defineEmits<ContextMenuSubContentEmits>()

const delegatedProps = reactiveOmit(props, 'class' as never)
const forwarded = useForwardPropsEmits(delegatedProps, emits)
</script>

<template>
  <ContextMenuSubContent
    class="ds-menu-content"
    data-test="ds-context-menu-sub-content"
    v-bind="forwarded"
  >
    <slot />
  </ContextMenuSubContent>
</template>
