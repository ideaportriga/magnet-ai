<script setup lang="ts">
</script>

<template>
  <div class="ds-sidebar__menu-badge" data-sidebar="menu-badge" data-test="ds-sidebar-menu-badge">
    <slot />
  </div>
</template>

<style>
.ds-sidebar__menu-badge {
  position: absolute;
  inset-inline-end: 4px;
  inset-block-start: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
  user-select: none;
  block-size: 20px;
  min-inline-size: 20px;
  padding-inline: var(--ds-space-2xs);
  font-size: var(--ds-font-size-xs);
  font-weight: var(--ds-font-weight-medium);
  color: var(--ds-color-text-grey);
  border-radius: var(--ds-radius-sm);
  font-variant-numeric: tabular-nums;
}
[data-collapsible='icon'] .ds-sidebar__menu-badge {
  display: none;
}
</style>
