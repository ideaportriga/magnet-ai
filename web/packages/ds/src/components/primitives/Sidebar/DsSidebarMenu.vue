<script setup lang="ts">
</script>

<template>
  <ul class="ds-sidebar__menu" data-sidebar="menu" data-test="ds-sidebar-menu">
    <slot />
  </ul>
</template>

<style>
.ds-sidebar__menu {
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-2xs);
  inline-size: 100%;
  min-inline-size: 0;
  margin: 0;
  padding: 0;
  list-style: "";
}
</style>
