<template lang="pug">
template(v-if='group')
  q-table.sticky-virtscroll-table.fit(
    flat,
    style='height: calc(100vh - 260px) !important',
    :rows='rows',
    :columns='columns',
    table-header-class='bg-secondary-bg',
    :row-key='rowKey',
    :selection='selection',
    v-model:selected='selectedCalc',
    :pagination='paginationRef',
    :rows-per-page-options='[0]',
    :selected-rows-label='() => ""',
    v-bind='visible',
    title-class='text-left',
    virtual-scroll,
    hide-header
  )
    template(v-slot:body='props')
      q-tr.cursor-pointer(
        :props='props',
        :className='activeRecordId == props.row?.id ? `bg-control-hover-bg` : ""',
        @click='props.expand = !props.expand'
      )
        template(v-if='subheader')
          component(:is='subheader.component', :row='props.row')
      q-tr.cursor-pointer(:props='props', :className='activeRecordId == props.row?.id ? `bg-control-hover-bg` : ""', v-show='props.expand')
        q-td.ba-border.padding-0(:colspan='columns.length + 1')
          km-table-new.fit(
            flat,
            virtual-scroll,
            :rows='props?.row?.records || []',
            :columns='columns',
            table-header-class='bg-secondary-bg',
            :row-key='rowKey',
            :selection='selection',
            v-model:selected='selectedCalc',
            :selected-rows-label='() => ""',
            v-bind='visible',
            title-class='text-left',
            hide-bottom
          )
template(v-else)
  q-table.sticky-virtscroll-table.fit(
    flat,
    :rows='rows',
    :columns='columns',
    style='height: calc(100vh - 260px) !important',
    table-header-class='bg-secondary-bg',
    :row-key='rowKey',
    :selection='selection',
    v-model:selected='selectedCalc',
    :pagination='pagination',
    :rows-per-page-options='[10]',
    :selected-rows-label='() => ""',
    v-bind='visible',
    title-class='text-left'
  )
    template(v-slot:header='scope')
      q-tr.bg-primary-light(:props='scope')
        q-th.ba-border(style='width: 20px')
          km-checkbox(v-model='scope.selected')
        q-th.ba-border(v-for='col in scope.cols', :key='col.name', :props='scope')
          span.km-title {{ col.label }}
    template(v-slot:body='props')
      q-tr.cursor-pointer(:props='props', :className='activeRecordId == props.row?.id ? `bg-control-hover-bg` : ""')
        q-td.ba-border
          km-checkbox(v-model='props.selected')
        q-td.ba-border.td-hoverable(v-for='col in props.cols', :key='col.name', :props='props', @click='$emit("selectRow", props.row)')
          template(v-if='col.type === "component"')
            component(:is='col.component', :row='props.row', :name='col.name')
          template(v-else-if='col.action') 
            a.km-label.text-primary(href='javascript:void(0)', @click='(e) => $emit("cellAction", { event: e, action: col.action, row: props.row })') {{ col.value }}
          template(v-else)
            span {{ col.value }}
</template>
<script>
import { defineComponent, ref } from 'vue'

export default defineComponent({
  props: {
    activeRecordId: {
      default: '',
      type: String,
    },
    selection: {
      default: 'single',
    },
    rowKey: {
      default: '',
    },
    columns: {
      default: [],
    },
    rows: {
      default: [],
    },
    visibleColumns: {
      default: false,
    },
    pagination: {
      default: {},
    },
    group: {
      default: false,
    },
    subheader: {},
  },
  emits: ['selectRow', 'cellAction', 'update:selected'],
  setup() {
    return {
      expanded: [],
      paginationRef: ref({
        rowsPerPage: 0,
      }),
    }
  },
  computed: {
    selectedCalc: {
      get() {
        return this.selected
      },
      set(value) {
        this.$emit('update:selected', value)
      },
    },
    visible() {
      return typeof this.visibleColumns === 'boolean' ? {} : { 'visible-columns': this.visibleColumns }
    },
  },
  methods: {
    getSubheader(cols, col) {
      console.log(cols, col, 'subheader')
      return cols.find((row) => row?.name == col)
    },
  },
})
</script>
<style lang="stylus">
.padding-0
    padding: 0 !important
.sticky-virtscroll-table
  /* height or max-height is important */
  height: 410px

  .q-table__top,
  .q-table__bottom,
  thead tr:first-child th /* bg color is important for th; just specify one */

  thead tr th
    position: sticky
    z-index: 1
  /* this will be the loading indicator */
  thead tr:last-child th
    /* height of all previous header rows */
    top: 48px
  thead tr:first-child th
    top: 0

  /* prevent scrolling behind sticky top row on focus */
  tbody
    /* height of all previous header rows */
    scroll-margin-top: 48px
</style>
