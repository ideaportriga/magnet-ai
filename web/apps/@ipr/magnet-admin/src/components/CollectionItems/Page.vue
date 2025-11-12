c
<template lang="pug">
.row.no-wrap.overflow-hidden.full-height
  .col
    .row.no-wrap.full-height.justify-center.fit
      .col-auto.collection-container
      .full-height.q-pb-md.relative-position.q-px-md(style='width: 1100px')
        .km-heading-4.q-mt-16.q-pl-12 Chunks
        .border.border-radius-12.bg-white.ba-border.q-my-16.q-pa-16.q-gap-16.full-width
          template(v-if='items.length && !loadingItems')
            .row.q-mb-12
              .col-auto.center-flex
                km-input(placeholder='Search', iconBefore='search', v-model='searchString', @input='searchString = $event', clearable)
            .row
              km-table(
                row-key='id',
                :columns='columns',
                :rows='visibleRows',
                selection='single',
                @selectRow='useDocuments.selectRecord($event.id)',
                :selected='selectedRow ? [selectedRow] : []',
                :visibleColumns='visibleColumns',
                :pagination='pagination'
              )
          template(v-else-if='loadingItems')
            .column.flex-center
              q-spinner.text-primary(size='40px')
          template(v-else)
            .column.flex-center
              .km-title.q-py-16.text-label Nothing in this knowledge source yet!
            km-icon(name='empty-collection', width='250', height='250')

  collection-items-drawer
</template>
<script>
import { useChroma } from '@shared'
import { defineComponent, ref } from 'vue'

export default defineComponent({
  setup() {
    const { items, searchString, pagination, visibleColumns, columns, visibleRows, selectedRow, ...useDocuments } = useChroma('documents')
    const { items: collections } = useChroma('collections')
    return {
      items,
      searchString,
      pagination,
      visibleColumns,
      columns,
      visibleRows,
      selectedRow,
      useDocuments,
      collections,
      loadingItems: ref(false),
    }
  },
  mounted() {
    this.requestItems()
  },
  methods: {
    async requestItems() {
      this.loadingItems = true
      const name = this.$route.params.id
      await this.useDocuments.get({ name })
      this.loadingItems = false
    },
  },
})
</script>
