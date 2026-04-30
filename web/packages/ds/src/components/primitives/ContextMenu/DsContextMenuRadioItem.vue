<script setup lang="ts">
import type { ContextMenuRadioItemEmits, ContextMenuRadioItemProps } from 'reka-ui'
import {
  ContextMenuItemIndicator,
  ContextMenuRadioItem,
  useForwardPropsEmits,
} from 'reka-ui'

const props = defineProps<ContextMenuRadioItemProps>()
const emits = defineEmits<ContextMenuRadioItemEmits>()

const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <ContextMenuRadioItem
    v-bind="forwarded"
    class="ds-menu-item ds-menu-item--radio"
    data-test="ds-context-menu-radio-item"
  >
    <span class="ds-menu-item-indicator">
      <ContextMenuItemIndicator>
        <slot name="indicator-icon">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 8 8"
            width="8"
            height="8"
            fill="currentColor"
            aria-hidden="true"
          >
            <circle cx="4" cy="4" r="4" />
          </svg>
        </slot>
      </ContextMenuItemIndicator>
    </span>
    <slot />
  </ContextMenuRadioItem>
</template>
