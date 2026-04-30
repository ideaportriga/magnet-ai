<script setup lang="ts">
/**
 * ComboboxItem — a selectable row inside ComboboxContent / ComboboxList.
 */
import type { ComboboxItemEmits, ComboboxItemProps } from 'reka-ui'
import { ComboboxItem, useForwardPropsEmits } from 'reka-ui'

const props = defineProps<ComboboxItemProps>()
const emits = defineEmits<ComboboxItemEmits>()

const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <ComboboxItem
    v-bind="forwarded"
    class="ds-combobox__item"
    data-test="ds-combobox-item"
  >
    <slot />
  </ComboboxItem>
</template>

<style>
.ds-combobox__item {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--ds-space-xs);
  padding-inline: var(--ds-space-xs);
  padding-block: var(--ds-space-2xs);
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-black);
  border-radius: var(--ds-radius-sm);
  outline: none;
  user-select: none;
  cursor: default;
}
.ds-combobox__item[data-highlighted] {
  background: var(--ds-color-accent-bg);
  color: var(--ds-color-accent);
}
.ds-combobox__item[data-disabled] {
  pointer-events: none;
  opacity: 0.5;
}
.ds-combobox__item > svg {
  flex: none;
  inline-size: 16px;
  block-size: 16px;
  pointer-events: none;
  color: var(--ds-color-text-grey);
}
</style>
