<script setup lang="ts">
/**
 * ComboboxContent — popper containing the dropdown items. Renders into a
 * portal and animates with [data-state] / [data-side] attributes.
 */
import type { ComboboxContentEmits, ComboboxContentProps } from 'reka-ui'
import { ComboboxContent, ComboboxPortal, useForwardPropsEmits } from 'reka-ui'

defineOptions({ inheritAttrs: false })

const props = withDefaults(defineProps<ComboboxContentProps>(), {
  position: 'popper',
  align: 'center',
  sideOffset: 4,
})
const emits = defineEmits<ComboboxContentEmits>()

const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <ComboboxPortal>
    <ComboboxContent
      v-bind="{ ...$attrs, ...forwarded }"
      class="ds-combobox__content"
      data-test="ds-combobox-content"
    >
      <slot />
    </ComboboxContent>
  </ComboboxPortal>
</template>

<style>
.ds-combobox__content {
  z-index: var(--ds-z-popover);
  inline-size: var(--reka-combobox-trigger-width, 200px);
  background: var(--ds-color-background);
  color: var(--ds-color-black);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
  box-shadow: var(--ds-shadow-md);
  outline: none;
  overflow: hidden;
  transform-origin: var(--reka-combobox-content-transform-origin);
  animation: ds-scale-in var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-combobox__content[data-state='closed'] {
  animation: ds-scale-out var(--ds-duration-fast) var(--ds-ease-in);
}
</style>
