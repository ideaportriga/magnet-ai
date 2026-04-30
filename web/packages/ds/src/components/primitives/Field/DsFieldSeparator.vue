<script setup lang="ts">
/**
 * FieldSeparator — horizontal divider between sections of a `DsFieldGroup`.
 * Optional slot renders centered text on top of the line (e.g. "OR").
 */

import DsSeparator from '../Separator/DsSeparator.vue'

defineSlots<{ default?: () => unknown }>()
</script>

<template>
  <div
    class="ds-field-separator"
    :data-content="!!$slots.default"
    data-test="ds-field-separator"
  >
    <DsSeparator class="ds-field-separator__line" orientation="horizontal" />
    <span
      v-if="$slots.default"
      class="ds-field-separator__content"
      data-test="ds-field-separator-content"
    >
      <slot />
    </span>
  </div>
</template>

<style>
.ds-field-separator {
  position: relative;
  block-size: 20px;
  margin-block: calc(var(--ds-space-sm) * -1);
  font-size: var(--ds-font-size-label);
}
.ds-field-separator__line {
  position: absolute;
  inset: 0;
  inset-block-start: 50%;
}
.ds-field-separator__content {
  position: relative;
  display: block;
  inline-size: fit-content;
  margin-inline: auto;
  padding-inline: var(--ds-space-sm);
  background: var(--ds-color-background);
  color: var(--ds-color-text-grey);
}
</style>
