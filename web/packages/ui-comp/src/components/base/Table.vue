<template lang="pug">
q-table.full-width(
  flat,
  :rows='rows',
  :columns='columns',
  table-header-class='bg-secondary-bg',
  :row-key='rowKey',
  selection='single',
  :selected='selected',
  :pagination='pagination',
  :rows-per-page-options='[10]',
  :selected-rows-label='() => ""',
  title-class='text-left',
  ref='table',
  :dense='dense',
  :sort-method='sortMethod',
  v-bind='mergedAttrs'
)
  template(v-slot:header='props')
    q-tr.bg-primary-light(:props='props')
      q-th.ba-border(v-for='col in props.cols', :key='col.name', :props='props')
        .row.inline
          div
            .km-title {{ col.label }}
            .km-subtitle.text-grey(v-if='col?.subLabel') {{ col.subLabel }}
  template(v-slot:body='props')
    q-tr(:props='props', data-test='table-row')
      q-td.ba-border.td-hoverable(v-for='col in props.cols', :key='col.name', :props='props', @click='$emit("selectRow", props.row)')
        template(v-if='col.type === "component"')
          component(:is='col.component', :row='props.row', :name='col.name')
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
      default: undefined
      ,
    },
  },
  emits: ['selectRow', 'cellAction'],
  computed: {
    mergedAttrs() {
      return {
        ...this.$attrs,
        ...(typeof this.visibleColumns === 'boolean' ? {} : { 'visible-columns': this.visibleColumns }),
      }
    },
  },
  methods: {
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
      return Promise.resolve() // Return a resolved promise instead of undefined
    },
  },
})
</script>

<style lang="stylus"></style>
