<script setup lang="ts">
/**
 * TableFooter — semantic <tfoot> styled as a summary row.
 */
</script>

<template>
  <tfoot class="ds-table__footer" data-test="ds-table-footer">
    <slot />
  </tfoot>
</template>

<style>
.ds-table__footer {
  background: var(--ds-color-light);
  border-block-start: 1px solid var(--ds-color-border);
  font-weight: var(--ds-font-weight-medium);
}
.ds-table__footer > tr:last-child {
  border-block-end: 0;
}
</style>
