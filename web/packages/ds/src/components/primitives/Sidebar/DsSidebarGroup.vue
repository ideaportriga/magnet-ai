<script setup lang="ts">
</script>

<template>
  <div class="ds-sidebar__group" data-sidebar="group" data-test="ds-sidebar-group">
    <slot />
  </div>
</template>

<style>
.ds-sidebar__group {
  position: relative;
  display: flex;
  flex-direction: column;
  inline-size: 100%;
  min-inline-size: 0;
  padding: var(--ds-space-sm);
}
</style>
