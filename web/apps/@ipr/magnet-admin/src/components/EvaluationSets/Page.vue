<template>
  <km-list-page>
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
      <evaluation-sets-create-new :show-new-dialog="showNewDialog" @cancel="showNewDialog = false" />
    </template>
  </km-list-page>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { usePermissions } from '@shared'
import { useDataTable } from '@/composables/useDataTable'
import { nameDescriptionColumn, chipCopyColumn, dateColumn } from '@/utils/columnHelpers'
import { m } from '@/paraglide/messages'
import type { EvaluationSet } from '@/types'

const router = useRouter()
const showNewDialog = ref(false)

const { can } = usePermissions()
const canCreate = computed(() => can('write:evaluations'))

const columns = [
  nameDescriptionColumn<EvaluationSet>(m.common_name()),
  chipCopyColumn<EvaluationSet>(m.common_systemName()),
  dateColumn<EvaluationSet>('created_at', m.common_created()),
  dateColumn<EvaluationSet>('updated_at', m.common_lastUpdated()),
]

const { table, isLoading, isFetching, globalFilter } = useDataTable<EvaluationSet>('evaluation_sets', columns, {
  defaultSort: [{ id: 'updated_at', desc: true }],
})

const openDetails = async (row: EvaluationSet) => {
  await router.push(`/evaluation-sets/${row.id}`)
}
</script>

