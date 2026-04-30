<template>
  <km-list-page>
    <template #toolbar>
      <div class="flex-none center-flex-y">
        <km-input data-test="search-input" :placeholder="m.common_search()" icon-before="search" :model-value="globalFilter" clearable @input="globalFilter = $event" />
      </div>
      <div class="km-space" />
      <div class="flex-none center-flex-y">
        <km-btn class="mr-md" data-test="new-btn" :label="m.common_new()" @click="showNewDialog = true" />
      </div>
    </template>
    <km-data-table :table="table" :loading="isLoading" :fetching="isFetching" fill-height row-key="id" @row-click="openDetails" />
    <template #overlays>
      <collections-create-new v-if="showNewDialog" :show-new-dialog="showNewDialog" @cancel="showNewDialog = false" />
    </template>
  </km-list-page>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useDataTable } from '@/composables/useDataTable'
import { nameDescriptionColumn, chipCopyColumn, dateColumn } from '@/utils/columnHelpers'
import { m } from '@/paraglide/messages'
import type { Collection } from '@/types'

const router = useRouter()
const showNewDialog = ref(false)

const columns = [
  nameDescriptionColumn<Collection>(m.common_name()),
  chipCopyColumn<Collection>(m.common_systemName()),
  dateColumn<Collection>('created_at', m.common_created()),
  dateColumn<Collection>('updated_at', m.common_lastUpdated()),
]

const { table, isLoading, isFetching, globalFilter } = useDataTable<Collection>('collections', columns, {
  defaultSort: [{ id: 'updated_at', desc: true }],
})

const openDetails = async (row: Collection) => {
  await router.push(`/knowledge-sources/${row.id}`)
}
</script>

