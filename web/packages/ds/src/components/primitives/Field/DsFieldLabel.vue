<script setup lang="ts">
/**
 * FieldLabel — `<label>` for the field's primary control. Re-exports
 * `DsLabel` semantics so clicking it focuses the bound control via `for`.
 */

import { Label, type LabelProps } from 'reka-ui'

defineProps<LabelProps>()
</script>

<template>
  <Label
    v-bind="$props"
    class="ds-field-label"
    data-test="ds-field-label"
  >
    <slot />
  </Label>
</template>

<style>
.ds-field-label {
  display: flex;
  inline-size: fit-content;
  align-items: center;
  gap: var(--ds-space-sm);
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  line-height: var(--ds-line-height-snug);
  color: var(--ds-color-label);
}
.ds-field[data-disabled='true'] .ds-field-label {
  opacity: 0.5;
}
</style>
