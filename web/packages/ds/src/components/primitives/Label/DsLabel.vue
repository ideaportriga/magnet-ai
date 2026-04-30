<script setup lang="ts">
/**
 * Label — accessible label. Wraps reka-ui `<Label>` so clicking the label
 * focuses the associated control via `for`/`htmlFor`.
 *
 *   <DsLabel for="email">Email</DsLabel>
 *   <DsInput id="email" v-model="email" />
 */

import { Label, type LabelProps } from 'reka-ui'

defineProps<LabelProps>()
</script>

<template>
  <Label
    v-bind="$props"
    class="ds-label"
    data-test="ds-label"
  >
    <slot />
  </Label>
</template>

<style>
.ds-label {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-sm);
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  line-height: var(--ds-line-height-none);
  color: var(--ds-color-label);
  user-select: none;
}

/* dim when the surrounding form group is disabled */
.ds-label[data-disabled='true'],
[data-disabled='true'] > .ds-label {
  opacity: 0.5;
  pointer-events: none;
}
</style>
