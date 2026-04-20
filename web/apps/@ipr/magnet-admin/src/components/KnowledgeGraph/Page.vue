<template>
  <div class="column no-wrap full-height q-page">
    <div class="collection-container kg-page-container q-mx-auto full-width column full-height q-px-md q-pt-16">
      <template v-if="isLoading && rows.length === 0">
        <div class="flex flex-center full-height">
          <q-spinner size="40px" color="primary" />
        </div>
      </template>
      <template v-else-if="rows.length">
        <div class="col ba-border border-radius-12 bg-white q-pa-16 column kg-table-wrapper">
          <div class="row q-mb-12">
            <div class="col-auto center-flex-y">
              <km-input data-test="search-input" :model-value="globalFilter" :placeholder="m.common_search()" icon-before="search" clearable @input="globalFilter = $event" />
            </div>
            <q-space />
            <div class="col-auto center-flex-y">
              <km-btn class="q-mr-12" data-test="new-btn" :label="m.common_new()" @click="showCreateDialog = true" />
            </div>
          </div>
          <div class="col kg-table-inner">
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
        <div class="row items-center justify-center">
          <div class="col-auto q-pa-xl bg-light border-radius-12">
            <div class="row items-center justify-center q-mb-md">
              <q-icon name="o_hub" size="48px" color="primary" />
            </div>
            <div class="km-heading-7 text-black">{{ m.knowledgeGraph_noGraphsYet() }}</div>
            <div class="km-description text-black">{{ m.knowledgeGraph_noGraphsYetDesc() }}</div>
            <div class="row items-center justify-center q-mt-lg">
              <km-btn data-test="new-btn" :label="m.knowledgeGraph_createKnowledgeGraph()" @click="showCreateDialog = true" />
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>

  <create-graph-dialog v-if="showCreateDialog" :show-dialog="showCreateDialog" @cancel="showCreateDialog = false" @created="handleGraphCreated" />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useQueryClient } from '@tanstack/vue-query'
import { useDataTable } from '@/composables/useDataTable'
import { textColumn, dateColumn } from '@/utils/columnHelpers'
import { entityKeys } from '@/queries/queryKeys'
import { m } from '@/paraglide/messages'
import type { KnowledgeGraph } from '@/types'
import CreateGraphDialog from './CreateGraphDialog.vue'

const router = useRouter()
const queryClient = useQueryClient()
const showCreateDialog = ref(false)

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
  max-width: 1200px;
}
.kg-table-wrapper,
.kg-table-inner {
  min-height: 0;
}
</style>
