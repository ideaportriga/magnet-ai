<script setup lang="ts">
</script>

<template>
  <div class="ds-sidebar__content" data-sidebar="content" data-test="ds-sidebar-content">
    <slot />
  </div>
</template>

<style>
.ds-sidebar__content {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-block-size: 0;
  gap: var(--ds-space-sm);
  overflow: auto;
}
[data-collapsible='icon'] .ds-sidebar__content {
  overflow: hidden;
}
</style>
