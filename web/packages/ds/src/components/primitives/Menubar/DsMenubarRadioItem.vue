<script setup lang="ts">
import type { MenubarRadioItemEmits, MenubarRadioItemProps } from 'reka-ui'
import {
  MenubarItemIndicator,
  MenubarRadioItem,
  useForwardPropsEmits,
} from 'reka-ui'

const props = defineProps<MenubarRadioItemProps>()
const emits = defineEmits<MenubarRadioItemEmits>()

const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <MenubarRadioItem
    v-bind="forwarded"
    class="ds-menu-item ds-menu-item--radio"
    data-test="ds-menubar-radio-item"
  >
    <span class="ds-menu-item-indicator">
      <MenubarItemIndicator>
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
      </MenubarItemIndicator>
    </span>
    <slot />
  </MenubarRadioItem>
</template>
