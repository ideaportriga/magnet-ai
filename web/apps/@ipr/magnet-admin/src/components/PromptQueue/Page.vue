<template>
  <km-list-page>
    <template #toolbar>
      <div class="flex-none center-flex-y">
        <km-input :placeholder="m.common_search()" icon-before="search" :model-value="globalFilter" clearable @input="globalFilter = $event" />
      </div>
      <div class="km-space" />
      <div class="flex-none center-flex-y">
        <km-btn v-if="canCreate" class="mr-md" :label="m.common_new()" @click="showNewDialog = true" />
      </div>
    </template>
    <km-data-table fill-height :table="table" row-key="id" @row-click="openDetails" />
    <template #overlays>
      <prompt-queue-create-new :show-new-dialog="showNewDialog" @cancel="showNewDialog = false" @created="onConfigCreated" />
    </template>
  </km-list-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { textColumn, chipCopyColumn, dateColumn } from '@/utils/columnHelpers'
import { m } from '@/paraglide/messages'
import PromptQueueCreateNew from './CreateNew.vue'
import { usePromptQueueStore } from '@/stores/promptQueueStore'
import { usePermissions } from '@shared'

const pqStore = usePromptQueueStore()
const router = useRouter()
const { can } = usePermissions()
const canCreate = computed(() => can('write:prompt_queue'))

const showNewDialog = ref(false)

const configs = computed(() => {
  const data = pqStore.promptQueueConfigs
  return Array.isArray(data) ? data : []
})

const columns = [
  textColumn('name', m.common_name()),
  chipCopyColumn(m.common_systemName()),
  textColumn('steps_count', 'Steps', {
    sortable: true,
    format: (val: unknown) => {
      // steps_count is computed from config.steps.length
      return val != null ? String(val) : '0'
    },
  }),
  dateColumn('created_at', m.common_created()),
  dateColumn('updated_at', m.common_lastUpdated()),
]

// Map data to add steps_count
const data = computed(() => {
  return configs.value.map((item: any) => ({
    ...item,
    steps_count: item?.config?.steps?.length ?? 0,
  }))
})

const { table, globalFilter } = useLocalDataTable(data, columns)

onMounted(async () => {
  await pqStore.fetchPromptQueueConfigs(true)
})

const openDetails = (row: any) => {
  router.push(`/prompt-queue/${row.id}`)
}

const onConfigCreated = (configId: string) => {
  router.push(`/prompt-queue/${configId}`)
}
</script>

<style scoped>
.prompt-queue-container {
  min-inline-size: 450px;
  max-inline-size: 1200px;
  inline-size: 100%;
}
</style>
