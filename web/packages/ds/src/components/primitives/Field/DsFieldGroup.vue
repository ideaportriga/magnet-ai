<script setup lang="ts">
/**
 * FieldGroup — vertical stack of `DsField` rows, used to lay out form
 * sections.
 */
</script>

<template>
  <div
    class="ds-field-group"
    data-test="ds-field-group"
  >
    <slot />
  </div>
</template>

<style>
.ds-field-group {
  display: flex;
  inline-size: 100%;
  flex-direction: column;
  gap: var(--ds-space-3xl);
  container-type: inline-size;
}
.ds-field-group [data-slot='checkbox-group'],
.ds-field-group [data-slot='radio-group'] {
  gap: var(--ds-space-md);
}
.ds-field-group > .ds-field-group {
  gap: var(--ds-space-lg);
}
</style>
