<script setup lang="ts">
/**
 * TableRow — semantic <tr> with hover + selected states.
 */
</script>

<template>
  <tr class="ds-table__row" data-test="ds-table-row">
    <slot />
  </tr>
</template>

<style>
.ds-table__row {
  border-block-end: 1px solid var(--ds-color-border);
  transition: background var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-table__row:hover {
  background: var(--ds-color-table-hover);
}
.ds-table__row[data-state='selected'] {
  background: var(--ds-color-table-active);
}
</style>
