<script setup lang="ts">
/**
 * NumberFieldInput — the actual native input element bound to NumberField state.
 */
import { NumberFieldInput } from 'reka-ui'
</script>

<template>
  <NumberFieldInput
    class="ds-number-field__input"
    data-test="ds-number-field-input"
  />
</template>

<style>
.ds-number-field__input {
  display: flex;
  block-size: 36px;
  inline-size: 100%;
  padding-block: var(--ds-space-2xs);
  padding-inline: var(--ds-space-sm);
  text-align: center;
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-black);
  background: transparent;
  border: 1px solid var(--ds-color-control-border);
  border-radius: var(--ds-radius-md);
  box-shadow: var(--ds-shadow-sm);
  transition:
    border-color var(--ds-duration-fast) var(--ds-ease-out),
    box-shadow var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-number-field__input::placeholder {
  color: var(--ds-color-placeholder);
}
.ds-number-field__input:focus-visible {
  outline: none;
  border-color: var(--ds-color-primary);
  box-shadow: 0 0 0 1px var(--ds-color-primary);
}
.ds-number-field__input:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}
</style>
