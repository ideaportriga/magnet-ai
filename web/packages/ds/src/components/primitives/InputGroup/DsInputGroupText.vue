<script setup lang="ts">
/**
 * InputGroupText — inline non-interactive text inside an addon (units,
 * prefixes, "@", etc).
 */
</script>

<template>
  <span class="ds-input-group__text" data-test="ds-input-group-text">
    <slot />
  </span>
</template>

<style>
.ds-input-group__text {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-sm);
  color: var(--ds-color-text-grey);
  font-size: var(--ds-font-size-label);
}
.ds-input-group__text > svg {
  pointer-events: none;
  inline-size: 16px;
  block-size: 16px;
}
</style>
