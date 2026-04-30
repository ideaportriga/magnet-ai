<script setup lang="ts">
/**
 * Drawer root — vaul-vue based slide-out sheet, pinned to bottom by default.
 * Mirrors the shadcn-vue Drawer API (DrawerRoot props/emits) but styled with
 * cube CSS tokens.
 *
 *   <DsDrawer v-model:open="open">
 *     <DsDrawerTrigger>Open</DsDrawerTrigger>
 *     <DsDrawerContent>
 *       <DsDrawerHeader>
 *         <DsDrawerTitle>Title</DsDrawerTitle>
 *         <DsDrawerDescription>...</DsDrawerDescription>
 *       </DsDrawerHeader>
 *       <DsDrawerFooter>
 *         <DsDrawerClose>Close</DsDrawerClose>
 *       </DsDrawerFooter>
 *     </DsDrawerContent>
 *   </DsDrawer>
 */

import type { DrawerRootEmits, DrawerRootProps } from 'vaul-vue'
import { useForwardPropsEmits } from 'reka-ui'
import { DrawerRoot } from 'vaul-vue'

const props = withDefaults(defineProps<DrawerRootProps>(), {
  shouldScaleBackground: true,
})

const emits = defineEmits<DrawerRootEmits>()

const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <DrawerRoot
    v-slot="slotProps"
    data-test="ds-drawer"
    v-bind="forwarded"
  >
    <slot v-bind="slotProps" />
  </DrawerRoot>
</template>
