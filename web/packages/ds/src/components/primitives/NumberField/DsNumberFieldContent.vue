<script setup lang="ts">
/**
 * NumberFieldContent — visual wrapper for the input + increment/decrement
 * controls. Pads the input so controls don't overlap the value.
 */
</script>

<template>
  <div class="ds-number-field__content" data-test="ds-number-field-content">
    <slot />
  </div>
</template>

<style>
.ds-number-field__content {
  position: relative;
}

/* Reserve space inside the input when increment/decrement controls exist */
.ds-number-field__content:has(.ds-number-field__increment) > .ds-number-field__input {
  padding-inline-end: var(--ds-space-2xl);
}
.ds-number-field__content:has(.ds-number-field__decrement) > .ds-number-field__input {
  padding-inline-start: var(--ds-space-2xl);
}
</style>
