<script setup lang="ts">
</script>

<template>
  <main class="ds-sidebar__inset" data-test="ds-sidebar-inset">
    <slot />
  </main>
</template>

<style>
.ds-sidebar__inset {
  position: relative;
  display: flex;
  flex-direction: column;
  flex: 1;
  inline-size: 100%;
  background: var(--ds-color-background);
}
@media (min-width: 768px) {
  .ds-sidebar-wrapper:has([data-variant='inset']) .ds-sidebar__inset {
    margin: var(--ds-space-sm);
    margin-inline-start: 0;
    border-radius: var(--ds-radius-xl);
    box-shadow: var(--ds-shadow-sm);
  }
}
</style>
