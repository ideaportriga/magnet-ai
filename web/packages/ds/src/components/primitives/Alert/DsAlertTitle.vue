<script setup lang="ts">
/** Alert title — bold one-liner; clamped to a single line. */
</script>

<template>
  <div class="ds-alert__title">
    <slot />
  </div>
</template>

<style>
.ds-alert__title {
  grid-column-start: 2;
  min-block-size: 1rem;
  font-weight: var(--ds-font-weight-medium);
  letter-spacing: -0.01em;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
