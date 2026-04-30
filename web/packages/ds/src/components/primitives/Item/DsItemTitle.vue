<script setup lang="ts">
/**
 * ItemTitle — primary label inside `DsItemContent`.
 */
</script>

<template>
  <div class="ds-item__title" data-test="ds-item-title">
    <slot />
  </div>
</template>

<style>
.ds-item__title {
  display: flex;
  inline-size: fit-content;
  align-items: center;
  gap: var(--ds-space-sm);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  line-height: var(--ds-line-height-snug);
  color: var(--ds-color-black);
}
</style>
