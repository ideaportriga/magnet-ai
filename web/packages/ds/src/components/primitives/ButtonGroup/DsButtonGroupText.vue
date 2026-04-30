<script setup lang="ts">
/**
 * ButtonGroupText — non-interactive text segment inside a button group
 * (labels, helper text, badges).
 */

import { Primitive, type PrimitiveProps } from 'reka-ui'

withDefaults(defineProps<PrimitiveProps>(), {
  as: 'div',
})
</script>

<template>
  <Primitive
    role="group"
    class="ds-button-group__text"
    :as="as"
    :as-child="asChild"
    data-test="ds-button-group-text"
  >
    <slot />
  </Primitive>
</template>

<style>
.ds-button-group__text {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-sm);
  background: var(--ds-color-light);
  border: 1px solid var(--ds-color-border);
  padding-inline: var(--ds-space-lg);
  border-radius: var(--ds-radius-md);
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  color: var(--ds-color-black);
  box-shadow: var(--ds-shadow-sm);
}
.ds-button-group__text > svg {
  pointer-events: none;
  inline-size: 16px;
  block-size: 16px;
  flex: none;
}
</style>
