<script setup lang="ts">
/**
 * ItemActions — trailing cluster of action controls (buttons, menus, etc).
 */
</script>

<template>
  <div class="ds-item__actions" data-test="ds-item-actions">
    <slot />
  </div>
</template>

<style>
.ds-item__actions {
  display: flex;
  align-items: center;
  gap: var(--ds-space-sm);
}
</style>
