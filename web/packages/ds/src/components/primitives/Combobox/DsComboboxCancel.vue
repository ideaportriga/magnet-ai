<script setup lang="ts">
/**
 * ComboboxCancel — clears the current ComboboxInput value when activated.
 * Re-export wrapper around Reka UI's ComboboxCancel.
 */
import type { ComboboxCancelProps } from 'reka-ui'
import { ComboboxCancel, useForwardProps } from 'reka-ui'

const props = defineProps<ComboboxCancelProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <ComboboxCancel
    v-bind="forwarded"
    class="ds-combobox__cancel"
    data-test="ds-combobox-cancel"
    aria-label="Clear combobox"
  >
    <slot>
      <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
        <path
          d="M2 2 L12 12 M12 2 L2 12"
          stroke="currentColor"
          stroke-width="1.6"
          stroke-linecap="round"
        />
      </svg>
    </slot>
  </ComboboxCancel>
</template>

<style>
.ds-combobox__cancel {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  inline-size: 20px;
  block-size: 20px;
  padding: 0;
  background: transparent;
  border: 0;
  color: var(--ds-color-text-grey);
  border-radius: var(--ds-radius-sm);
  cursor: pointer;
  transition: background var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-combobox__cancel:hover {
  background: var(--ds-color-control-hover-bg);
  color: var(--ds-color-black);
}
</style>
