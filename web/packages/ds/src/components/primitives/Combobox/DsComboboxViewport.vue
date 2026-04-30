<script setup lang="ts">
/**
 * ComboboxViewport — scrollable region inside the ComboboxContent popper.
 */
import type { ComboboxViewportProps } from 'reka-ui'
import { ComboboxViewport, useForwardProps } from 'reka-ui'

const props = defineProps<ComboboxViewportProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <ComboboxViewport
    v-bind="forwarded"
    class="ds-combobox__viewport"
    data-test="ds-combobox-viewport"
  >
    <slot />
  </ComboboxViewport>
</template>

<style>
.ds-combobox__viewport {
  max-block-size: 300px;
  scroll-padding-block: var(--ds-space-2xs);
  overflow-inline: hidden;
  overflow-block: auto;
}
</style>
