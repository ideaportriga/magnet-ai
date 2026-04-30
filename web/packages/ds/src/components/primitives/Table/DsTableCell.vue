<script setup lang="ts">
/**
 * TableCell — semantic <td>.
 */
</script>

<template>
  <td class="ds-table__cell" data-test="ds-table-cell">
    <slot />
  </td>
</template>

<style>
.ds-table__cell {
  padding: var(--ds-space-xs);
  vertical-align: middle;
  white-space: nowrap;
}
.ds-table__cell:has([role='checkbox']) {
  padding-inline-end: 0;
}
.ds-table__cell > [role='checkbox'] {
  transform: translateY(2px);
}
</style>
