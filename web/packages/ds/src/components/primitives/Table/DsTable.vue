<script setup lang="ts">
/**
 * Table — semantic HTML <table> wrapped in a horizontally scrollable container.
 */
</script>

<template>
  <div class="ds-table__container" data-test="ds-table-container">
    <table class="ds-table" data-test="ds-table">
      <slot />
    </table>
  </div>
</template>

<style>
.ds-table__container {
  position: relative;
  inline-size: 100%;
  overflow: auto;
}

.ds-table {
  inline-size: 100%;
  caption-side: bottom;
  font-size: var(--ds-font-size-label);
  border-collapse: collapse;
  color: var(--ds-color-black);
}
</style>
