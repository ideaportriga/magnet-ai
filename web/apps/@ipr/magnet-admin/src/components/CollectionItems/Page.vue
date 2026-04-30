<template>
  <div class="cluster overflow-hidden full-height" data-wrap="no">
    <div class="flex-1 stack full-height" data-gap="0">
      <div class="collection-container mx-auto full-width stack full-height px-md pt-lg" data-gap="0">
        <div class="km-heading-4 pl-md">{{ m.common_chunks() }}</div>
        <template v-if="rows.length &amp;&amp; !isLoading">
          <div class="cluster mb-md mt-md">
            <div class="flex-none center-flex">
              <km-input :placeholder="m.common_search()" icon-before="search" :model-value="globalFilter" clearable @input="globalFilter = $event" />
            </div>
          </div>
          <div class="flex-1 ba-border border-radius-12 bg-white p-lg" style="min-block-size: 0">
            <km-data-table :table="table" fill-height row-key="id" :active-row-id="selectedId" @row-click="onSelectRecord" />
          </div>
        </template>
        <template v-else-if="isLoading">
          <div class="flex" style="flex-direction: column; justify-content: center; align-items: center">
            <km-loader size="40px" />
          </div>
        </template>
        <template v-else>
          <div class="flex" style="flex-direction: column; justify-content: center; align-items: center">
            <div class="km-title py-lg text-label">{{ m.collectionItems_nothingInSourceYet() }}</div>
          </div>
          <km-icon name="empty-collection" width="250" height="250" />
        </template>
      </div>
    </div>
    <collection-items-drawer />
  </div>
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
