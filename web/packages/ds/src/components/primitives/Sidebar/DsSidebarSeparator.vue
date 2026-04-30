<script setup lang="ts">
import DsSeparator from '../Separator/DsSeparator.vue'
</script>

<template>
  <DsSeparator
    class="ds-sidebar__separator"
    data-sidebar="separator"
    data-test="ds-sidebar-separator"
  />
</template>

<style>
.ds-sidebar__separator {
  margin-inline: var(--ds-space-sm);
  inline-size: auto;
  background: var(--ds-color-border);
}
</style>
