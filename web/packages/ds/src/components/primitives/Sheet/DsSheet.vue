<script setup lang="ts">
/**
 * Sheet — side-anchored modal panel built on Reka UI's Dialog. The visible
 * surface is `<DsSheetContent :side="…">`; this root just owns open state.
 */
import type { DialogRootEmits, DialogRootProps } from 'reka-ui'
import { DialogRoot, useForwardPropsEmits } from 'reka-ui'

const props = defineProps<DialogRootProps>()
const emits = defineEmits<DialogRootEmits>()

const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <DialogRoot v-slot="slotProps" v-bind="forwarded">
    <slot v-bind="slotProps" />
  </DialogRoot>
</template>
