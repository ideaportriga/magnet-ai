<script setup lang="ts">
/**
 * ComboboxList — wrapper sitting between ComboboxContent and the items.
 * In Reka UI this is conceptually `ComboboxContent`; in DS we expose a
 * separate `Content` (popper portal) and a `List` (scroll viewport) so
 * consumers can compose with ComboboxAnchor + ComboboxContent + List
 * + Viewport + Item.
 *
 * Implementation note: this just renders the ComboboxViewport. If you don't
 * need a separate viewport you can use DsComboboxViewport directly.
 */
import type { ComboboxViewportProps } from 'reka-ui'
import { ComboboxViewport, useForwardProps } from 'reka-ui'

const props = defineProps<ComboboxViewportProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <ComboboxViewport
    v-bind="forwarded"
    class="ds-combobox__list"
    data-test="ds-combobox-list"
  >
    <slot />
  </ComboboxViewport>
</template>

<style>
.ds-combobox__list {
  max-block-size: 300px;
  scroll-padding-block: var(--ds-space-2xs);
  overflow-inline: hidden;
  overflow-block: auto;
}
</style>
