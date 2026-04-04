<template lang="pug">
.row.no-wrap.overflow-hidden.full-height
  .col.column.no-wrap.full-height
    .collection-container.q-mx-auto.full-width.column.full-height.q-px-md.q-pt-16
      .km-heading-4.q-pl-12 {{ m.common_chunks() }}
      template(v-if='rows.length && !isLoading')
        .row.q-mb-12.q-mt-md
          .col-auto.center-flex
            km-input(:placeholder='m.common_search()', iconBefore='search', :modelValue='globalFilter', @input='globalFilter = $event', clearable)
        .col.ba-border.border-radius-12.bg-white.q-pa-16(style='min-height: 0')
          km-data-table(
            :table='table',
            fill-height,
            row-key='id',
            :activeRowId='selectedId',
            @row-click='onSelectRecord'
          )
      template(v-else-if='isLoading')
        .column.flex-center
          q-spinner(size='40px', color='primary')
      template(v-else)
        .column.flex-center
          .km-title.q-py-16.text-label {{ m.collectionItems_nothingInSourceYet() }}
        km-icon(name='empty-collection', width='250', height='250')
  collection-items-drawer
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useRoute } from 'vue-router'
import { useEntityQueries } from '@/queries/entities'
import { useDataTable } from '@/composables/useDataTable'
import { textColumn, dateColumn } from '@/utils/columnHelpers'
import type { Document } from '@/types'

const route = useRoute()
const selectedId = ref<string | null>(null)

const columns = [
  textColumn<Document>('title' as keyof Document, m.common_title(), {
    format: (val) => {
      if (val && typeof val === 'object') return (val as Record<string, unknown>)?.title as string ?? '-'
      return val ? String(val) : '-'
    },
  }),
  dateColumn<Document>('created_at', m.common_created()),
  dateColumn<Document>('updated_at', m.common_lastUpdated()),
]

const extraParams = computed(() => ({
  collection_id: route.params.id as string,
}))

const { table, rows, isLoading, isFetching, globalFilter } = useDataTable<Document>('documents', columns, {
  extraParams,
})

function onSelectRecord(row: Document) {
  selectedId.value = row.id
}
</script>
