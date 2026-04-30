<script setup lang="ts">
/**
 * PinInputInput — single character cell. Multiple cells stitch together as
 * one continuous input via the rounded-corner edge rules.
 */
import type { PinInputInputProps } from 'reka-ui'
import { PinInputInput, useForwardProps } from 'reka-ui'

const props = defineProps<PinInputInputProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <PinInputInput
    v-bind="forwarded"
    class="ds-pin-input__input"
    data-test="ds-pin-input-input"
  />
</template>

<style>
.ds-pin-input__input {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  inline-size: 36px;
  block-size: 36px;
  text-align: center;
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-black);
  background: transparent;
  border: 1px solid var(--ds-color-control-border);
  border-inline-start-width: 0;
  outline: none;
  box-shadow: var(--ds-shadow-sm);
  transition:
    border-color var(--ds-duration-fast) var(--ds-ease-out),
    box-shadow var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-pin-input__input:first-child {
  border-inline-start-width: 1px;
  border-start-start-radius: var(--ds-radius-md);
  border-end-start-radius: var(--ds-radius-md);
}
.ds-pin-input__input:last-child {
  border-start-end-radius: var(--ds-radius-md);
  border-end-end-radius: var(--ds-radius-md);
}
.ds-pin-input__input:focus-visible {
  z-index: var(--ds-z-raised);
  border-color: var(--ds-color-primary);
  box-shadow: 0 0 0 3px var(--ds-color-primary-transparent);
}
.ds-pin-input__input[aria-invalid='true'] {
  border-color: var(--ds-color-error);
}
.ds-pin-input__input[aria-invalid='true']:focus-visible {
  box-shadow: 0 0 0 3px var(--ds-color-error-bg);
}
</style>
