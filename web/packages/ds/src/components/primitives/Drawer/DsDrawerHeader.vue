<script setup lang="ts">
</script>

<template>
  <div class="ds-drawer__header" data-test="ds-drawer-header">
    <slot />
  </div>
</template>

<style>
.ds-drawer__header {
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-xs);
  padding: var(--ds-space-lg);
}
</style>
