<script setup lang="ts">
/**
 * BreadcrumbItem — single segment in a breadcrumb trail.
 */
</script>

<template>
  <li
    class="ds-breadcrumb__item"
    data-test="ds-breadcrumb-item"
  >
    <slot />
  </li>
</template>

<style>
.ds-breadcrumb__item {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-xs);
}
</style>
