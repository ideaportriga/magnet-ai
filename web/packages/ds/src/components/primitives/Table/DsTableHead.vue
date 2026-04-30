<script setup lang="ts">
/**
 * TableHead — semantic <th> column header.
 */
</script>

<template>
  <th class="ds-table__head" data-test="ds-table-head">
    <slot />
  </th>
</template>

<style>
.ds-table__head {
  block-size: 40px;
  padding-inline: var(--ds-space-xs);
  text-align: start;
  vertical-align: middle;
  font-weight: var(--ds-font-weight-medium);
  white-space: nowrap;
  color: var(--ds-color-black);
}
.ds-table__head:has([role='checkbox']) {
  padding-inline-end: 0;
}
.ds-table__head > [role='checkbox'] {
  transform: translateY(2px);
}
</style>
