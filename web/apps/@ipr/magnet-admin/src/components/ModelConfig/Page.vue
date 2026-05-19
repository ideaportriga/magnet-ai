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
        <km-input data-test="search-input" :placeholder="m.common_search()" icon-before="search" :model-value="globalFilter" clearable @input="globalFilter = $event" />
      </div>
      <div class="km-space" />
      <div class="flex-none center-flex-y">
        <km-btn v-if="canCreate" class="mr-md" data-test="new-btn" :label="m.common_new()" @click="showNewDialog = true" />
      </div>
    </template>
    <km-data-table :table="table" :loading="isLoading" :fetching="isFetching" fill-height row-key="id" @row-click="openDetails" />
    <template #overlays>
      <model-config-create-new v-if="showNewDialog" :show-new-dialog="showNewDialog" :type="tab" @cancel="showNewDialog = false" />
    </template>
  </km-list-page>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDataTable } from '@/composables/useDataTable'
import { textColumn, componentColumn, dateColumn } from '@/utils/columnHelpers'
import { m } from '@/paraglide/messages'
import { useEntityAccess } from '@/composables/useEntityAccess'
import type { Model } from '@/types'
import Check from '@/config/model/component/Check.vue'
import Features from '@/config/model/component/Features.vue'

const router = useRouter()
const { canCreate } = useEntityAccess('model')
const showNewDialog = ref(false)
const tab = ref('prompts')
const tabs = [
  { name: 'prompts', label: 'Chat Completion Models' },
  { name: 'embeddings', label: 'Vector Embedding Models' },
  { name: 're-ranking', label: 'Reranking Models' },
]

const allColumns = [
  textColumn<Model>('display_name', 'Display name'),
  textColumn<Model>('model', m.common_name(), { sortable: true }),
  componentColumn<Model>('features', 'Features', Features, {
    props: (row) => ({ name: 'features' }),
  }),
  componentColumn<Model>('is_default', 'Default', Check, {
    accessorKey: 'is_default',
    sortable: true,
    align: 'center',
    props: (row) => ({ name: 'is_default' }),
  }),
  dateColumn<Model>('created_at', m.common_created()),
  dateColumn<Model>('updated_at', m.common_lastUpdated()),
]

const extraParams = computed(() => ({ type: tab.value }))

const { table, rows, isLoading, isFetching, globalFilter } = useDataTable<Model>('model', allColumns, {
  defaultSort: [{ id: 'updated_at', desc: true }],
  extraParams,
  dataFilter: (items: Model[]) => {
    // Pin is_default rows to the top
    return [...items].sort((a, b) => {
      if (a.is_default && !b.is_default) return -1
      if (!a.is_default && b.is_default) return 1
      return 0
    })
  },
})

const openDetails = async (row: Model) => {
  await router.push(`/model/${row.id}`)
}
</script>
