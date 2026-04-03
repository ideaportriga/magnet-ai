<template lang="pug">
.column.no-wrap.full-height
  .collection-container.q-mx-auto.full-width.column.full-height.q-px-md.q-pt-16
    .col.ba-border.border-radius-12.bg-white.q-pa-16.column(style='min-height: 0')
      .row.q-mb-12
        .col-auto.center-flex-y
          km-input(placeholder='Search', iconBefore='search', :modelValue='globalFilter', @input='globalFilter = $event', clearable)
        q-space
        .col-auto.center-flex-y
          km-btn.q-mr-12(label='New', @click='showNewDialog = true')
      .col(style='min-height: 0')
        km-data-table(
          :table='table',
          :loading='isLoading', :fetching='isFetching',
          fill-height,
          row-key='id',
          @row-click='openDetails'
        )
  api-keys-create-new(:showNewDialog='showNewDialog', @cancel='showNewDialog = false')
  km-popup-confirm(
    :visible='showConfirmDialog',
    confirmButtonLabel='Ok, delete',
    cancelButtonLabel='Cancel',
    notificationIcon='fas fa-triangle-exclamation',
    @confirm='deleteSelected',
    @cancel='showConfirmDialog = false'
  )
    .row.item-center.justify-center.km-heading-7.q-mb-md {{ deleteTitle }}
    .row.text-center.justify-center Access granted by this key will be immediately revoked, and any applications or services using it will no longer be able to connect. This action cannot be undone.
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDataTable } from '@/composables/useDataTable'
import { textColumn, dateColumn } from '@/utils/columnHelpers'
import { useEntityQueries } from '@/queries/entities'
import type { ApiKey } from '@/types'

const router = useRouter()
const showNewDialog = ref(false)
const showConfirmDialog = ref(false)
const selected = ref<ApiKey[]>([])

const { api_keys: apiKeysQ } = useEntityQueries()
const { mutateAsync: removeApiKey } = apiKeysQ.useRemove()

const columns = [
  textColumn<ApiKey>('name', 'Name'),
  textColumn<ApiKey>('value_masked', 'Key', {
    format: (val) => val ? `................${val}` : '-',
  }),
  dateColumn<ApiKey>('created_at', 'Created'),
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
