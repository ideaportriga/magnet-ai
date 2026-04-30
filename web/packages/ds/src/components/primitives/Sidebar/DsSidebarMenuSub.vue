<script setup lang="ts">
</script>

<template>
  <ul class="ds-sidebar__menu-sub" data-sidebar="menu-sub" data-test="ds-sidebar-menu-sub">
    <slot />
  </ul>
</template>

<style>
.ds-sidebar__menu-sub {
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-2xs);
  margin: 0;
  margin-inline: 14px;
  padding: 0;
  padding-inline: 10px;
  padding-block: 2px;
  list-style: "";
  min-inline-size: 0;
  border-inline-start: 1px solid var(--ds-color-border);
  transform: translateX(1px);
}
[data-collapsible='icon'] .ds-sidebar__menu-sub {
  display: none;
}
</style>
