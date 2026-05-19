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
      <api-keys-create-new :show-new-dialog="showNewDialog" @cancel="showNewDialog = false" />
      <km-popup-confirm :visible="showConfirmDialog" confirm-button-label="Ok, delete" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="deleteSelected" @cancel="showConfirmDialog = false">
        <div class="cluster km-heading-7 mb-md" data-justify="center">{{ deleteTitle }}</div>
        <div class="cluster text-center" data-justify="center">Access granted by this key will be immediately revoked, and any applications or services using it will no longer be able to connect. This action cannot be undone.</div>
      </km-popup-confirm>
    </template>
  </km-list-page>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDataTable } from '@/composables/useDataTable'
import { textColumn, dateColumn } from '@/utils/columnHelpers'
import { useEntityQueries } from '@/queries/entities'
import { m } from '@/paraglide/messages'
import { useEntityAccess } from '@/composables/useEntityAccess'
import type { ApiKey } from '@/types'

const router = useRouter()
const { canCreate } = useEntityAccess('api_keys')
const showNewDialog = ref(false)
const showConfirmDialog = ref(false)
const selected = ref<ApiKey[]>([])

const { api_keys: apiKeysQ } = useEntityQueries()
const { mutateAsync: removeApiKey } = apiKeysQ.useRemove()

const columns = [
  textColumn<ApiKey>('name', m.common_name()),
  textColumn<ApiKey>('value_masked', m.common_key(), {
    format: (val) => val ? `................${val}` : '-',
  }),
  dateColumn<ApiKey>('created_at', m.common_created()),
]

const { table, rows, isLoading, isFetching, globalFilter } = useDataTable<ApiKey>('api_keys', columns)

const deleteTitle = computed(() => {
  if (selected.value.length === 1) {
    return 'You are about to delete an API Key'
  }
  return `You are about to delete ${selected.value.length} API Keys`
})

const openDetails = async (row: ApiKey) => {
  await router.push(`/api-keys/${row.id}`)
}

const deleteSelected = async () => {
  await Promise.all(selected.value.map((item) => removeApiKey(item.id!)))
  selected.value = []
  showConfirmDialog.value = false
}
</script>
