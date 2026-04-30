<script setup lang="ts">
/**
 * FieldSet — semantic `<fieldset>` wrapper for related fields, paired with
 * `DsFieldLegend`.
 */
</script>

<template>
  <fieldset class="ds-field-set" data-test="ds-field-set">
    <slot />
  </fieldset>
</template>

<style>
.ds-field-set {
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-2xl);
  margin: 0;
  padding: 0;
  border: 0;
  min-inline-size: 0;
}
.ds-field-set:has([data-slot='checkbox-group']),
.ds-field-set:has([data-slot='radio-group']) {
  gap: var(--ds-space-md);
}
</style>
