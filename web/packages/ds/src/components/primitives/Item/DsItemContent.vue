<script setup lang="ts">
/**
 * ItemContent — main body cluster (title + description) of a `DsItem`.
 */
</script>

<template>
  <div class="ds-item__content" data-test="ds-item-content">
    <slot />
  </div>
</template>

<style>
.ds-item__content {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  gap: var(--ds-space-2xs);
  min-inline-size: 0;
}
.ds-item__content + .ds-item__content {
  flex: none;
}
</style>
