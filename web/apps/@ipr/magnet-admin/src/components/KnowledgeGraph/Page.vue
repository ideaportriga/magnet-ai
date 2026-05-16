<template>
  <div class="stack full-height km-page" data-gap="0">
    <div class="collection-container kg-page-container mx-auto full-width stack full-height px-md pt-lg" data-gap="0">
      <template v-if="isLoading && rows.length === 0">
        <div class="flex flex-center full-height">
          <km-loader size="40px" />
        </div>
      </template>
      <template v-else-if="rows.length">
        <div class="flex-1 ba-border border-radius-12 bg-white p-lg stack kg-table-wrapper" data-gap="0">
          <div class="cluster mb-md">
            <div class="flex-none center-flex-y">
              <km-input data-test="search-input" :model-value="globalFilter" :placeholder="m.common_search()" icon-before="search" clearable @input="globalFilter = $event" />
            </div>
            <div class="km-space" />
            <div class="flex-none center-flex-y">
              <km-btn v-if="canCreate" class="mr-md" data-test="new-btn" :label="m.common_new()" @click="showCreateDialog = true" />
            </div>
          </div>
          <div class="flex-1 kg-table-inner">
            <km-data-table
              :table="table"
              :loading="isLoading"
              :fetching="isFetching"
              fill-height
              row-key="id"
              @row-click="openDetails"
            />
          </div>
        </div>
      </template>
      <template v-else>
        <div class="cluster" data-justify="center">
          <div class="flex-none p-xl bg-light border-radius-12">
            <div class="cluster mb-md" data-justify="center">
              <km-glyph name="graph" size="48px" tone="brand" />
            </div>
            <div class="km-heading-7 text-black">{{ m.knowledgeGraph_noGraphsYet() }}</div>
            <div class="km-description text-black">{{ m.knowledgeGraph_noGraphsYetDesc() }}</div>
            <div class="cluster mt-lg" data-justify="center">
              <km-btn v-if="canCreate" data-test="new-btn" :label="m.knowledgeGraph_createKnowledgeGraph()" @click="showCreateDialog = true" />
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>

  <create-graph-dialog v-if="showCreateDialog" :show-dialog="showCreateDialog" @cancel="showCreateDialog = false" @created="handleGraphCreated" />
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useQueryClient } from '@tanstack/vue-query'
import { usePermissions } from '@shared'
import { useDataTable } from '@/composables/useDataTable'
import { textColumn, dateColumn } from '@/utils/columnHelpers'
import { entityKeys } from '@/queries/queryKeys'
import { m } from '@/paraglide/messages'
import type { KnowledgeGraph } from '@/types'
import CreateGraphDialog from './CreateGraphDialog.vue'

const router = useRouter()
const queryClient = useQueryClient()
const showCreateDialog = ref(false)

const { can } = usePermissions()
const canCreate = computed(() => can('write:knowledge_graph'))

const columns = [
  textColumn<KnowledgeGraph>('name', m.common_name()),
  textColumn<KnowledgeGraph>('documents_count', 'Documents', { align: 'right' }),
  dateColumn<KnowledgeGraph>('created_at', m.common_created()),
]

const { table, rows, isLoading, isFetching, globalFilter } = useDataTable<KnowledgeGraph>('knowledge_graph', columns, {
  manualPagination: false,
  manualSorting: false,
  manualFiltering: false,
})

const openDetails = (row: KnowledgeGraph) => {
  router.push(`/knowledge-graph/${row.id}`)
}

const handleGraphCreated = (result: KnowledgeGraph) => {
  showCreateDialog.value = false
  queryClient.invalidateQueries({ queryKey: entityKeys.knowledge_graph.all })
  if (result?.id) {
    router.push(`/knowledge-graph/${result.id}`)
  }
}
</script>

<style scoped>
.kg-page-container {
  max-inline-size: 1200px;
}
.kg-table-wrapper,
.kg-table-inner {
  min-block-size: 0;
}
</style>
