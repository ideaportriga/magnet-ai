<script setup lang="ts">
/**
 * ResizablePanelGroup — flex container holding ResizablePanel + ResizableHandle.
 * Built on Reka UI's SplitterGroup.
 */
import type { SplitterGroupEmits, SplitterGroupProps } from 'reka-ui'
import { SplitterGroup, useForwardPropsEmits } from 'reka-ui'

const props = defineProps<SplitterGroupProps>()
const emits = defineEmits<SplitterGroupEmits>()

const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <SplitterGroup
    v-slot="slotProps"
    v-bind="forwarded"
    class="ds-resizable"
    data-test="ds-resizable"
  >
    <slot v-bind="slotProps" />
  </SplitterGroup>
</template>

<style>
.ds-resizable {
  display: flex;
  inline-size: 100%;
  block-size: 100%;
}
.ds-resizable[data-orientation='vertical'] {
  flex-direction: column;
}
</style>
