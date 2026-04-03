<template lang="pug">
.column.full-height(v-if='data?.length', style='min-height: 0')
  .row.q-mb-12.q-gap-12
    .col-auto.center-flex-y
      km-input(:placeholder='m.common_search()', iconBefore='search', :modelValue='globalFilter', @input='globalFilter = $event', clearable)
    q-space
    .col-auto
      template(v-if='selectedRows.length > 0')
        km-btn(@click='showDeleteDialog = true', icon='delete', flat, :label='m.common_delete()')
    .col-auto
      km-btn(:label='m.apiServers_addTools()', @click='showNewDialog = true')
  .col(style='min-height: 0')
    km-data-table(:table='table', fill-height, row-key='system_name', @row-click='handleRowClick')
template(v-else)
  .column.justify-center.items-center.full-width.full-height
    .col.q-pa-xl.bg-light.border-radius-12
      .row.items-center.justify-center.q-mb-md
        q-icon(name='fa fa-arrow-right-arrow-left', size='48px', color='primary')
      .km-heading-7.text-black {{ m.apiServers_noApiToolsYet() }}
      .km-description.text-black {{ m.apiServers_useApiSpec() }}
      .row.items-center.justify-center.q-mt-lg
        km-btn(:label='m.apiServers_addTools()', @click='showNewDialog = true')
api-servers-new-tools(:showNewDialog='showNewDialog', @cancel='showNewDialog = false')
km-popup-confirm(
  :visible='showDeleteDialog',
  :confirmButtonLabel='m.common_delete()',
  :cancelButtonLabel='m.common_cancel()',
  notificationIcon='fas fa-triangle-exclamation',
  @confirm='deleteSelected',
  @cancel='showDeleteDialog = false'
)
  .km-title.q-pl-16.q-pb-8.q-pt-lg.text-text-grey.text-center {{ m.apiServers_deleteToolsConfirm() }}
  .km-description.q-pl-16.q-pb-8.q-pt-lg.text-text-grey.text-center {{ m.apiServers_actionCannotBeUndone() }}
</template>

<script setup>
import { computed, ref } from 'vue'
import { m } from '@/paraglide/messages'
import { useRouter, useRoute } from 'vue-router'
import { fetchData } from '@shared'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { selectionColumn, nameDescriptionColumn, chipCopyColumn } from '@/utils/columnHelpers'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useAppStore } from '@/stores/appStore'

const router = useRouter()
const route = useRoute()
const { draft, updateField } = useEntityDetail('api_servers')
const appStore = useAppStore()
const showNewDialog = ref(false)
const showDeleteDialog = ref(false)

const data = computed(() => draft.value?.tools ?? [])

const columns = [
  selectionColumn(),
  nameDescriptionColumn(m.common_nameDescription()),
  chipCopyColumn(m.common_systemName()),
]

const { table, globalFilter, selectedRows, clearSelection } = useLocalDataTable(data, columns, {
  enableRowSelection: true,
})

const handleRowClick = (row) => {
  router.push(`${route.path}/tools/${row.system_name}`)
}

const deleteSelected = async () => {
  const removedTools = selectedRows.value.map((tool) => tool.system_name)
  const remainingTools = data.value.filter((tool) => !removedTools.includes(tool.system_name))
  const id = draft.value?.id
  await fetchData({
    endpoint: appStore.config.api.aiBridge.urlAdmin,
    service: `api_servers/${id}`,
    method: 'PATCH',
    credentials: 'include',
    body: JSON.stringify({ tools: remainingTools }),
  })
  updateField('tools', remainingTools)
  clearSelection()
  showDeleteDialog.value = false
}
</script>
