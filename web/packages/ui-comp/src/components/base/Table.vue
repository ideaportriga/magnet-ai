<template lang="pug">
q-table.full-width(
  :class='{ "sticky-virtscroll-table": isVirtualScroll }',
  :style='isVirtualScroll ? "flex: 1; min-height: 0; height: 100%" : ""',
  flat,
  :rows='rows',
  :columns='columns',
  table-header-class='bg-primary-light',
  :row-key='rowKey',
  :selection='selection',
  v-model:selected='selectedCalc',
  :pagination='isVirtualScroll ? virtualScrollPagination : pagination',
  :rows-per-page-options='isVirtualScroll ? [0] : [10]',
  :virtual-scroll='isVirtualScroll',
  :virtual-scroll-item-size='virtualScrollItemSize',
  :selected-rows-label='() => ""',
  title-class='text-left',
  ref='table',
  :dense='dense',
  :sort-method='sortMethod',
  v-bind='mergedAttrs',
  @virtual-scroll='onVirtualScroll'
)
  template(v-slot:header='props')
    q-tr.bg-primary-light(:props='props')
      q-th.ba-border(v-if='selection === "multiple"', style='width: 20px')
        km-checkbox(v-model='props.selected')
      q-th.ba-border(v-for='col in props.cols', :key='col.name', :props='props')
        .row.inline
          div
            .km-title {{ col.label }}
            .km-subtitle.text-grey(v-if='col?.subLabel') {{ col.subLabel }}
  template(v-slot:body='props')
    q-tr(
      :props='props',
      data-test='table-row',
      :class='{ "cursor-pointer": selection === "multiple", "bg-control-hover-bg": activeRecordId && activeRecordId == props.row?.[rowKey] }'
    )
      q-td.ba-border(v-if='selection === "multiple"')
        km-checkbox(v-model='props.selected')
      q-td.ba-border.td-hoverable(v-for='col in props.cols', :key='col.name', :props='props', @click='$emit("selectRow", props.row)')
        template(v-if='col.type === "component"')
          component(:is='col.component', :row='props.row', :name='col.name')
        template(v-else-if='col.type === "drilldown"')
          .flex
            km-btn(
              icon='fas fa-chevron-right',
              icon-size='14px',
              flat,
              @click='(e) => $emit("cellAction", { event: e, action: col.action, row: props.row })'
            )
        template(v-else-if='col.action')
          a.km-label.text-primary(href='javascript:void(0)', @click='(e) => $emit("cellAction", { event: e, action: col.action, row: props.row })') {{ col.value }}
        template(v-else)
          span(:class='col.class') {{ col.value }}
</template>

<script>
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'QTableWrapper',

  inheritAttrs: false,
  props: {
    rowKey: {
      type: String,
      default: '',
    },
    selected: {
      type: Array,
      default: () => [],
    },
    columns: {
      type: Array,
      default: () => [],
    },
    rows: {
      type: Array,
      default: () => [],
    },
    visibleColumns: {
      type: [Boolean, Object],
      default: false,
    },
    pagination: {
      type: Object,
      default: () => ({}),
    },
    dense: {
      type: Boolean,
      default: false,
    },
    sortMethod: {
      type: Function,
      default: undefined,
    },
    fillHeight: {
      type: Boolean,
      default: false,
    },
    virtualScrollItemSize: {
      type: Number,
      default: 48,
    },
    selection: {
      type: String,
      default: 'single',
      validator: (v) => ['single', 'multiple', 'none'].includes(v),
    },
    activeRecordId: {
      type: [String, Number],
      default: '',
    },
  },
  emits: ['selectRow', 'cellAction', 'virtual-scroll', 'update:selected'],
  computed: {
    isVirtualScroll() {
      return this.fillHeight
    },
    virtualScrollPagination() {
      return { rowsPerPage: 0, page: 1 }
    },
    selectedCalc: {
      get() {
        return this.selected
      },
      set(value) {
        this.$emit('update:selected', value)
      },
    },
    mergedAttrs() {
      return {
        ...this.$attrs,
        ...(typeof this.visibleColumns === 'boolean' ? {} : { 'visible-columns': this.visibleColumns }),
        // When using server-side filtering, provide a no-op filter method
        // to prevent Quasar from trying to apply client-side filtering
        // which fails when filter is an object instead of a string
        'filter-method': this.noOpFilterMethod,
      }
    },
  },
  methods: {
    onVirtualScroll(details) {
      this.$emit('virtual-scroll', details)
    },
    noOpFilterMethod(rows) {
      // Always return all rows - filtering is done server-side
      return rows
    },
    getTableRows() {
      return this.$refs.table.filteredSortedRows
    },
    setPagination(page) {
      this.$refs.table.setPagination({ page })
    },
    goToRow(rowKey) {
      const rowIndex = this.getTableRows().findIndex((row) => row[this.rowKey] === rowKey)
      const rowsPerPage = this.pagination.rowsPerPage || 10
      const page = Math.floor(rowIndex / rowsPerPage) + 1
      this.setPagination(page)
      return rowIndex
    },
    getRowIndex(row) {
      return this.$refs.table.getRowIndex(row)
    },
    requestServerInteraction(...args) {
      if (this.$refs.table && typeof this.$refs.table.requestServerInteraction === 'function') {
        return this.$refs.table.requestServerInteraction(...args)
      }
      console.warn("Inner <q-table> doesn't have requestServerInteraction or is not yet mounted")
      return Promise.resolve()
    },
  },
})
</script>

<style lang="stylus"></style>
