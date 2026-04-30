<script setup lang="ts">
/**
 * Collapsible — show/hide a region of content. Compose with
 * `DsCollapsibleTrigger` and `DsCollapsibleContent`.
 *
 *   <DsCollapsible v-model:open="isOpen">
 *     <DsCollapsibleTrigger>Toggle</DsCollapsibleTrigger>
 *     <DsCollapsibleContent>Hidden body</DsCollapsibleContent>
 *   </DsCollapsible>
 */

import {
  CollapsibleRoot,
  type CollapsibleRootEmits,
  type CollapsibleRootProps,
  useForwardPropsEmits,
} from 'reka-ui'

const props = defineProps<CollapsibleRootProps>()
const emits = defineEmits<CollapsibleRootEmits>()

const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <CollapsibleRoot
    v-slot="slotProps"
    v-bind="forwarded"
    class="ds-collapsible"
    data-test="ds-collapsible"
  >
    <slot v-bind="slotProps" />
  </CollapsibleRoot>
</template>

<style>
.ds-collapsible {
  display: block;
}
</style>
