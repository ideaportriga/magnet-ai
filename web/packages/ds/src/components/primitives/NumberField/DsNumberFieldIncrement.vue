<script setup lang="ts">
/**
 * NumberFieldIncrement — plus button. Default content is an inline plus icon.
 */
import type { NumberFieldIncrementProps } from 'reka-ui'
import { NumberFieldIncrement, useForwardProps } from 'reka-ui'

const props = defineProps<NumberFieldIncrementProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <NumberFieldIncrement
    v-bind="forwarded"
    class="ds-number-field__increment"
    data-test="ds-number-field-increment"
  >
    <slot>
      <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
        <path
          d="M3 8 L13 8 M8 3 L8 13"
          stroke="currentColor"
          stroke-width="1.6"
          stroke-linecap="round"
        />
      </svg>
    </slot>
  </NumberFieldIncrement>
</template>

<style>
.ds-number-field__increment {
  position: absolute;
  inset-block-start: 50%;
  inset-inline-end: 0;
  transform: translateY(-50%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  inline-size: var(--ds-space-2xl);
  block-size: var(--ds-space-2xl);
  padding: var(--ds-space-sm);
  background: transparent;
  border: 0;
  color: var(--ds-color-icon);
  cursor: pointer;
  border-radius: var(--ds-radius-sm);
  transition: background var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-number-field__increment:hover {
  background: var(--ds-color-control-hover-bg);
}
.ds-number-field__increment:disabled {
  cursor: not-allowed;
  opacity: 0.2;
}
</style>
