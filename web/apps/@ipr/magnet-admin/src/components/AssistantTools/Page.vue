<template>
  <km-list-page>
    <template #tabs>
      <km-tabs v-model="tab" class="bb-border full-width mb-lg" narrow-indicator dense align="left" no-caps content-class="km-tabs">
        <template v-for="t in tabs" :key="t">
          <km-tab :name="t.name" :label="t.label" />
        </template>
      </km-tabs>
    </template>
    <template #toolbar>
      <div class="flex-none center-flex-y">
        <km-input :placeholder="m.common_search()" icon-before="search" :model-value="globalFilter" clearable @input="globalFilter = $event" />
      </div>
      <div class="km-space" />
      <div class="flex-none center-flex-y">
        <km-btn class="mr-md" :label="m.common_new()" @click="showNewDialog = true" />
      </div>
    </template>
    <km-data-table :table="table" :loading="isLoading" :fetching="isFetching" fill-height row-key="id" @row-click="openDetails" />
    <template #overlays>
      <assistant-tools-create-new :show-new-dialog="showNewDialog && tab == 'api'" @cancel="showNewDialog = false" />
      <assistant-tools-create-new-rag :show-new-dialog="showNewDialog && tab == 'rag'" @cancel="showNewDialog = false" />
    </template>
  </km-list-page>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDataTable } from '@/composables/useDataTable'
import { nameDescriptionColumn, chipCopyColumn, dateColumn } from '@/utils/columnHelpers'
import { m } from '@/paraglide/messages'
import type { AssistantTool } from '@/types'

const router = useRouter()
const showNewDialog = ref(false)
const tab = ref('api')
const tabs = [
  { name: 'api', label: 'API' },
  { name: 'rag', label: 'RAG' },
]

const columns = [
  nameDescriptionColumn<AssistantTool>(m.common_name()),
  chipCopyColumn<AssistantTool>(m.common_systemName()),
  dateColumn<AssistantTool>('created_at', m.common_created()),
  dateColumn<AssistantTool>('updated_at', m.common_lastUpdated()),
]

const extraParams = computed(() => ({ type: tab.value }))

const { table, rows, isLoading, isFetching, globalFilter } = useDataTable<AssistantTool>('assistant_tools', columns, {
  defaultSort: [{ id: 'updated_at', desc: true }],
  extraParams,
})

const openDetails = async (row: AssistantTool) => {
  await router.push(`/assistant-tools/${row.id}`)
}
</script>

