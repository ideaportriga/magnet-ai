<script setup lang="ts">
/**
 * ComboboxAnchor — visual anchor element the ComboboxContent positions against.
 */
import type { ComboboxAnchorProps } from 'reka-ui'
import { ComboboxAnchor, useForwardProps } from 'reka-ui'

const props = defineProps<ComboboxAnchorProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <ComboboxAnchor
    v-bind="forwarded"
    class="ds-combobox__anchor"
    data-test="ds-combobox-anchor"
  >
    <slot />
  </ComboboxAnchor>
</template>

<style>
.ds-combobox__anchor {
  inline-size: 200px;
}
</style>
