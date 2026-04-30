<script setup lang="ts">
/**
 * BreadcrumbList — ordered list wrapper for breadcrumb items.
 */
</script>

<template>
  <ol
    class="ds-breadcrumb__list"
    data-test="ds-breadcrumb-list"
  >
    <slot />
  </ol>
</template>

<style>
.ds-breadcrumb__list {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--ds-space-xs);
  list-style: "";
  margin: 0;
  padding: 0;
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-text-grey);
  overflow-wrap: break-word;
}

@media (min-width: 640px) {
  .ds-breadcrumb__list { gap: var(--ds-space-sm); }
}
</style>
