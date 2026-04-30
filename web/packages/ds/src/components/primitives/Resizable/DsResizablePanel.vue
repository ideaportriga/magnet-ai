<script setup lang="ts">
/**
 * ResizablePanel — a single resizable region inside a panel group.
 */
import type { SplitterPanelEmits, SplitterPanelProps } from 'reka-ui'
import { SplitterPanel, useForwardExpose, useForwardPropsEmits } from 'reka-ui'

const props = defineProps<SplitterPanelProps>()
const emits = defineEmits<SplitterPanelEmits>()

const forwarded = useForwardPropsEmits(props, emits)
const { forwardRef } = useForwardExpose()
</script>

<template>
  <SplitterPanel
    :ref="forwardRef"
    v-slot="slotProps"
    v-bind="forwarded"
    data-test="ds-resizable-panel"
  >
    <slot v-bind="slotProps" />
  </SplitterPanel>
</template>
