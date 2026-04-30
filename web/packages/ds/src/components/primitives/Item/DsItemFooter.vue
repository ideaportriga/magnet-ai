<script setup lang="ts">
/**
 * ItemFooter — bottom row spanning the full width of the `DsItem`.
 */
</script>

<template>
  <div class="ds-item__footer" data-test="ds-item-footer">
    <slot />
  </div>
</template>

<style>
.ds-item__footer {
  display: flex;
  flex-basis: 100%;
  align-items: center;
  justify-content: space-between;
  gap: var(--ds-space-sm);
}
</style>
