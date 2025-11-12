<template lang="pug">
.row.no-wrap.overflow-hidden.full-height
  q-scroll-area.fit
    .row.no-wrap.full-height.justify-center.fit
      .col-auto.collection-container
        .full-height.q-pb-md.relative-position.q-px-md
          .border.border-radius-12.bg-white.ba-border.q-my-16.q-pa-16.q-gap-16.full-width
            .row.q-mb-12
              .col-auto.center-flex-y
                km-input(placeholder='Search', iconBefore='search', v-model='searchString', @input='searchString = $event', clearable) 
              q-space
              .col-auto.center-flex-y
                km-btn.q-mr-12(label='New', @click='showNewDialog = true')
            .row
              km-table(
                @selectRow='openDetails',
                selection='single',
                row-key='id',
                :selected='selectedRow ? [selectedRow] : []',
                :columns='columns',
                :rows='visibleRows ?? []',
                @cellAction='cellAction',
                :visibleColumns='visibleColumns',
                style='min-width: 1100px',
                ref='table',
                :pagination='pagination'
              )

collections-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false')
</template>

<script>
import { ref } from 'vue'
import { useChroma } from '@shared'
import { beforeRouteEnter } from '@/guards'
export default {
  beforeRouteEnter,
  setup() {
    const { items, searchString, selected, pagination, visibleColumns, columns, visibleRows, selectedRow, ...useCollection } =
      useChroma('collections')

    return {
      items,
      searchString,
      selected,
      pagination,
      visibleColumns,
      columns,
      visibleRows,
      selectedRow,
      useCollection,
      createNew: ref(false),
      loadingRefresh: ref(false),
      showNewDialog: ref(false),
    }
  },
  methods: {
    async openDetails(row) {
      await this.$router.push(`/knowledge-sources/${row.id}`)
    },
    async openCreateNew() {
      if (this.selected) {
        this.closeDrawer()
        await new Promise((resolve) => setTimeout(resolve, 900))
      }
      this.createNew = true
    },
    cellAction({ event, action, row }) {
      event.stopPropagation()
      if (action === 'drilldown') this.$router.push(`/knowledge-sources/${row.id}/items`)
    },
    async refreshTable() {
      this.loadingRefresh = true
      this.useCollection.get()
      this.loadingRefresh = false
    },
    closeDrawer() {
      this.useCollection.selectRecord(null)
    },
  },
}
</script>

<style lang="stylus">
.collection-container {
  min-width: 450px;
  max-width: 1200px;
  width: 100%;
}
.km-input:not(.q-field--readonly) .q-field__control::before
  background: #fff !important;
</style>
