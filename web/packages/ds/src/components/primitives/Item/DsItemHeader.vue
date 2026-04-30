<script setup lang="ts">
/**
 * ItemHeader — top row spanning the full width of the `DsItem` (e.g. meta).
 */
</script>

<template>
  <div class="ds-item__header" data-test="ds-item-header">
    <slot />
  </div>
</template>

<style>
.ds-item__header {
  display: flex;
  flex-basis: 100%;
  align-items: center;
  justify-content: space-between;
  gap: var(--ds-space-sm);
}
</style>
