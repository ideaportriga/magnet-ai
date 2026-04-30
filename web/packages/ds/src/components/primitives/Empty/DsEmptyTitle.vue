<script setup lang="ts">
/**
 * EmptyTitle — primary heading of an empty state.
 */
</script>

<template>
  <div class="ds-empty__title" data-test="ds-empty-title">
    <slot />
  </div>
</template>

<style>
.ds-empty__title {
  font-size: var(--ds-font-size-body-lg);
  font-weight: var(--ds-font-weight-medium);
  letter-spacing: -0.01em;
  color: var(--ds-color-black);
}
</style>
