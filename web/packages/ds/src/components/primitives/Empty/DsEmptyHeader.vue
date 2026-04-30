<script setup lang="ts">
/**
 * EmptyHeader — header cluster (media + title + description) of an empty state.
 */
</script>

<template>
  <div class="ds-empty__header" data-test="ds-empty-header">
    <slot />
  </div>
</template>

<style>
.ds-empty__header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--ds-space-sm);
  max-inline-size: 24rem;
  text-align: center;
}
</style>
