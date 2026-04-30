<script setup lang="ts">
</script>

<template>
  <div class="ds-sidebar__section ds-sidebar__header" data-sidebar="header" data-test="ds-sidebar-header">
    <slot />
  </div>
</template>

<style>
.ds-sidebar__section {
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-sm);
  padding: var(--ds-space-sm);
}
</style>
