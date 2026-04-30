<script setup lang="ts">
/**
 * TableEmpty — single-row "no data" placeholder spanning the full table.
 */
import DsTableCell from './DsTableCell.vue'
import DsTableRow from './DsTableRow.vue'

withDefaults(
  defineProps<{
    colspan?: number
  }>(),
  {
    colspan: 1,
  },
)
</script>

<template>
  <DsTableRow>
    <DsTableCell :colspan="colspan" class="ds-table__empty" data-test="ds-table-empty">
      <div class="ds-table__empty-inner">
        <slot />
      </div>
    </DsTableCell>
  </DsTableRow>
</template>

<style>
.ds-table__empty {
  padding: var(--ds-space-md);
  white-space: nowrap;
  vertical-align: middle;
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-black);
}
.ds-table__empty-inner {
  display: flex;
  align-items: center;
  justify-content: center;
  padding-block: var(--ds-space-3xl);
}
</style>
