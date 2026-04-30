<script setup lang="ts">
/**
 * NumberFieldDecrement — minus button. Default content is an inline minus icon.
 */
import type { NumberFieldDecrementProps } from 'reka-ui'
import { NumberFieldDecrement, useForwardProps } from 'reka-ui'

const props = defineProps<NumberFieldDecrementProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <NumberFieldDecrement
    v-bind="forwarded"
    class="ds-number-field__decrement"
    data-test="ds-number-field-decrement"
  >
    <slot>
      <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
        <path d="M3 8 L13 8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
      </svg>
    </slot>
  </NumberFieldDecrement>
</template>

<style>
.ds-number-field__decrement {
  position: absolute;
  inset-block-start: 50%;
  inset-inline-start: 0;
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
.ds-number-field__decrement:hover {
  background: var(--ds-color-control-hover-bg);
}
.ds-number-field__decrement:disabled {
  cursor: not-allowed;
  opacity: 0.2;
}
</style>
