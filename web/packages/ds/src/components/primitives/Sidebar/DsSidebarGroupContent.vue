<script setup lang="ts">
</script>

<template>
  <div class="ds-sidebar__group-content" data-sidebar="group-content" data-test="ds-sidebar-group-content">
    <slot />
  </div>
</template>

<style>
.ds-sidebar__group-content {
  inline-size: 100%;
  font-size: var(--ds-font-size-label);
}
</style>
