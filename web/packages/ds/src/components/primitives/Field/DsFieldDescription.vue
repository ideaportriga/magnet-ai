<script setup lang="ts">
/**
 * FieldDescription — helper text rendered beneath a field's control.
 */
</script>

<template>
  <p class="ds-field-description" data-test="ds-field-description">
    <slot />
  </p>
</template>

<style>
.ds-field-description {
  margin: 0;
  color: var(--ds-color-text-grey);
  font-size: var(--ds-font-size-label);
  line-height: var(--ds-line-height-normal);
  font-weight: var(--ds-font-weight-regular);
}
.ds-field-description > a {
  color: inherit;
  text-decoration: underline;
  text-underline-offset: 4px;
}
.ds-field-description > a:hover { color: var(--ds-color-primary); }
</style>
