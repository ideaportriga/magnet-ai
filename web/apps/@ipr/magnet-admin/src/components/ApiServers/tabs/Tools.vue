<template>
  <div v-if="data?.length" class="stack full-height" data-gap="0" style="min-block-size: 0">
    <div class="cluster mb-md" data-gap="md">
      <div class="flex-none center-flex-y">
        <km-input :placeholder="m.common_search()" icon-before="search" :model-value="globalFilter" clearable @input="globalFilter = $event" />
      </div>
      <div class="km-space" />
      <div class="flex-none">
        <template v-if="!apiServerReadonly && selectedRows.length &gt; 0">
          <km-btn icon="delete" flat :label="m.common_delete()" @click="showDeleteDialog = true" />
        </template>
      </div>
      <div class="flex-none">
        <km-btn v-if="!apiServerReadonly" :label="m.apiServers_addTools()" @click="showNewDialog = true" />
      </div>
    </div>
    <div class="flex-1" style="min-block-size: 0">
      <km-data-table :table="table" fill-height row-key="system_name" @row-click="handleRowClick" />
    </div>
  </div>
  <template v-else>
    <div class="flex full-width full-height" style="flex-direction: column; justify-content: center; align-items: center">
      <div class="flex-1 p-xl bg-light border-radius-12">
        <div class="cluster mb-md" data-justify="center">
          <km-glyph name="swap" size="48px" tone="brand" />
        </div>
        <div class="km-heading-7 text-black">{{ m.apiServers_noApiToolsYet() }}</div>
        <div class="km-description text-black">{{ m.apiServers_useApiSpec() }}</div>
        <div class="cluster mt-lg" data-justify="center">
          <km-btn v-if="!apiServerReadonly" :label="m.apiServers_addTools()" @click="showNewDialog = true" />
        </div>
      </div>
    </div>
  </template>
  <api-servers-new-tools :show-new-dialog="showNewDialog" @cancel="showNewDialog = false" />
  <km-popup-confirm :visible="showDeleteDialog" :confirm-button-label="m.common_delete()" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="deleteSelected" @cancel="showDeleteDialog = false">
    <div class="km-title pl-lg pb-sm pt-lg text-text-grey text-center">{{ m.apiServers_deleteToolsConfirm() }}</div>
    <div class="km-description pl-lg pb-sm pt-lg text-text-grey text-center">{{ m.apiServers_actionCannotBeUndone() }}</div>
  </km-popup-confirm>
</template>

<script setup>
import { computed, inject, ref } from 'vue'
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
const apiServerReadonlyRef = inject('apiServerReadonly', null)
const apiServerReadonly = computed(() => Boolean(apiServerReadonlyRef?.value))
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
  if (apiServerReadonly.value) return
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
