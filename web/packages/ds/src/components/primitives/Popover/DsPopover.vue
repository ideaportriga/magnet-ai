<script setup lang="ts">
/**
 * Popover primitive — Reka UI Popover with the same anchor/positioning
 * controls as DsDropdownMenu. Use this for transient, non-menu floating
 * content (filters, hint cards, mini-forms).
 */

import {
  PopoverArrow,
  PopoverClose,
  PopoverContent,
  PopoverPortal,
  PopoverRoot,
  PopoverTrigger,
} from 'reka-ui'

withDefaults(
  defineProps<{
    open?: boolean
    placement?: 'bottom' | 'top' | 'left' | 'right'
    align?: 'start' | 'center' | 'end'
    sideOffset?: number
    showArrow?: boolean
    /** When set, the popover content gets a fixed width. */
    width?: number | string
  }>(),
  {
    placement: 'bottom',
    align: 'center',
    sideOffset: 6,
    showArrow: false,
  },
)

defineEmits<{
  'update:open': [value: boolean]
}>()

defineSlots<{
  trigger?: () => unknown
  default?: () => unknown
}>()
</script>

<template>
  <PopoverRoot
    :open="open"
    @update:open="$emit('update:open', $event)"
  >
    <PopoverTrigger as-child>
      <slot name="trigger" />
    </PopoverTrigger>

    <PopoverPortal>
      <PopoverContent
        class="ds-popover"
        :side="placement"
        :align="align"
        :side-offset="sideOffset"
        :style="{ inlineSize: typeof width === 'number' ? `${width}px` : width }"
        data-test="ds-popover"
      >
        <slot />
        <PopoverArrow v-if="showArrow" class="ds-popover__arrow" />
      </PopoverContent>
    </PopoverPortal>
  </PopoverRoot>
</template>

<script lang="ts">
export const PopoverCloseButton = PopoverClose
</script>

<style>
.ds-popover {
  z-index: var(--ds-z-popover);
  padding: var(--ds-space-md);
  background: var(--ds-color-panel-main-bg);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
  box-shadow: var(--ds-shadow-md);
  outline: none;
  animation: ds-menu-in var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-popover[data-state='closed'] {
  animation: ds-menu-out var(--ds-duration-instant) var(--ds-ease-in);
}
.ds-popover__arrow { fill: var(--ds-color-panel-main-bg); }
</style>
