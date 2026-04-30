<script setup lang="ts">
/**
 * `<km-table>` — minimal table wrapper. Replaces simple uses of Quasar's
 * `<q-table>` where the consumer renders rows via slots. For data-driven
 * tables with sorting/pagination prefer `<KmDataTable>`.
 *
 * Slots:
 *   - `header` — `<thead>` content
 *   - default — `<tbody>` content
 *   - `footer` — `<tfoot>` content
 */
withDefaults(
  defineProps<{
    dense?: boolean
    bordered?: boolean
    flat?: boolean
  }>(),
  { dense: false, bordered: false, flat: false },
)
</script>

<template>
  <div
    class="km-table"
    :data-dense="dense ? 'true' : undefined"
    :data-bordered="bordered ? 'true' : undefined"
    :data-flat="flat ? 'true' : undefined"
    data-test="km-table"
  >
    <table class="km-table__table">
      <thead v-if="$slots.header" class="km-table__head"><slot name="header" /></thead>
      <tbody class="km-table__body"><slot /></tbody>
      <tfoot v-if="$slots.footer" class="km-table__foot"><slot name="footer" /></tfoot>
    </table>
  </div>
</template>

<style>
.km-table {
  inline-size: 100%;
  overflow: auto;
  overscroll-behavior: contain;
  border-radius: var(--ds-radius-md, 8px);
  background: var(--ds-color-white);
}
.km-table[data-bordered='true'] { border: 1px solid var(--ds-color-border); }
.km-table__table {
  inline-size: 100%;
  border-collapse: collapse;
}
.km-table__head th {
  text-align: start;
  font-weight: var(--ds-font-weight-medium, 500);
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-text-grey);
  padding: var(--ds-space-sm, 8px) var(--ds-space-md, 12px);
  border-block-end: 1px solid var(--ds-color-border);
  background: var(--ds-color-table-header, var(--ds-color-light));
}
.km-table__body td {
  padding: var(--ds-space-sm, 8px) var(--ds-space-md, 12px);
  border-block-end: 1px solid var(--ds-color-border);
}
.km-table__body tr:last-child td { border-block-end: 0; }
.km-table__body tr:hover { background: var(--ds-color-table-hover, var(--ds-color-light)); }
.km-table[data-dense='true'] .km-table__head th,
.km-table[data-dense='true'] .km-table__body td {
  padding: var(--ds-space-xs, 4px) var(--ds-space-sm, 8px);
}
</style>
