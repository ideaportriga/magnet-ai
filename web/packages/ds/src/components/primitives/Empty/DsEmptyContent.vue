<script setup lang="ts">
/**
 * EmptyContent — actions / supplementary content area beneath the header.
 */
</script>

<template>
  <div class="ds-empty__content" data-test="ds-empty-content">
    <slot />
  </div>
</template>

<style>
.ds-empty__content {
  display: flex;
  inline-size: 100%;
  min-inline-size: 0;
  max-inline-size: 24rem;
  flex-direction: column;
  align-items: center;
  gap: var(--ds-space-md);
  text-wrap: balance;
  font-size: var(--ds-font-size-label);
}
</style>
