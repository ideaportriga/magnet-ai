<template>
  <div class="stack full-height" data-gap="0">
    <div class="collection-container mx-auto full-width stack full-height px-md pt-lg" data-gap="0">
      <div class="flex-1 ba-border border-radius-12 bg-white p-lg stack" data-gap="0" style="min-block-size: 0">
        <div class="cluster mb-md">
          <div class="flex-none center-flex-y">
            <km-input data-test="search-input" :placeholder="m.common_search()" icon-before="search" :model-value="globalFilter" clearable @input="globalFilter = $event" />
          </div>
          <div class="km-space" />
          <div class="flex-none center-flex-y">
            <km-btn class="mr-md" data-test="new-btn" :label="m.common_new()" @click="showNewDialog = true" />
          </div>
        </div>
        <div class="flex-1" style="min-block-size: 0">
          <km-data-table :table="table" :loading="isLoading" :fetching="isFetching" fill-height row-key="id" @row-click="openDetails" />
        </div>
      </div>
      <rag-create-new :show-new-dialog="showNewDialog" @cancel="showNewDialog = false" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useDataTable } from '@/composables/useDataTable'
import { nameDescriptionColumn, chipCopyColumn, dateColumn } from '@/utils/columnHelpers'
import { m } from '@/paraglide/messages'
import type { RagTool } from '@/types'

const router = useRouter()
const showNewDialog = ref(false)

const columns = [
  nameDescriptionColumn<RagTool>(m.common_name()),
  chipCopyColumn<RagTool>(m.common_systemName()),
  dateColumn<RagTool>('created_at', m.common_created()),
  dateColumn<RagTool>('updated_at', m.common_lastUpdated()),
]

const { table, isLoading, isFetching, globalFilter } = useDataTable<RagTool>('rag_tools', columns, {
  defaultSort: [{ id: 'updated_at', desc: true }],
})

const openDetails = async (row: RagTool) => {
  await router.push(`/rag-tools/${row.id}`)
}
</script>

