<script setup lang="ts">
/**
 * BreadcrumbPage — current (non-interactive) page in the breadcrumb trail.
 */
</script>

<template>
  <span
    class="ds-breadcrumb__page"
    role="link"
    aria-disabled="true"
    aria-current="page"
    data-test="ds-breadcrumb-page"
  >
    <slot />
  </span>
</template>

<style>
.ds-breadcrumb__page {
  color: var(--ds-color-black);
  font-weight: var(--ds-font-weight-regular);
}
</style>
