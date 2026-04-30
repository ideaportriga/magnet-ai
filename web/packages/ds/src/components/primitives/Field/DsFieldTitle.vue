<script setup lang="ts">
/**
 * FieldTitle — non-interactive label-style heading for grouped controls (e.g.
 * checkbox groups) where there is no single `<label for>` target.
 */
</script>

<template>
  <div class="ds-field-title" data-test="ds-field-title">
    <slot />
  </div>
</template>

<style>
.ds-field-title {
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
.ds-field[data-disabled='true'] .ds-field-title {
  opacity: 0.5;
}
</style>
