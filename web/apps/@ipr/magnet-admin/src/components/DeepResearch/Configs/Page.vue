<template>
  <km-list-page>
    <template #toolbar>
      <div class="flex-none center-flex-y">
        <km-input :placeholder="m.common_search()" icon-before="search" :model-value="globalFilter" clearable @input="globalFilter = $event" />
      </div>
      <div class="km-space" />
      <div class="flex-none center-flex-y">
        <km-btn class="mr-md" :label="m.common_new()" @click="showNewDialog = true" />
      </div>
    </template>
    <km-data-table fill-height :table="table" row-key="id" @row-click="openDetails" />
    <template #overlays>
      <deep-research-configs-create-new :show-new-dialog="showNewDialog" @cancel="showNewDialog = false" @created="onConfigCreated" />
    </template>
  </km-list-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { m } from '@/paraglide/messages'
import { useRouter } from 'vue-router'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { textColumn, chipCopyColumn, dateColumn } from '@/utils/columnHelpers'
import DeepResearchCreateNew from './CreateNew.vue'
import { useDeepResearchStore } from '@/stores/deepResearchStore'

const drStore = useDeepResearchStore()
const router = useRouter()

onMounted(() => drStore.fetchConfigs())

const showNewDialog = ref(false)

const configs = computed(() => {
  const configsData = drStore.configs
  return Array.isArray(configsData) ? configsData : []
})

const columns = [
  textColumn('name', m.common_name()),
  chipCopyColumn(m.common_systemName()),
  dateColumn('created_at', m.common_created()),
  dateColumn('updated_at', m.common_lastUpdated()),
]

const { table, globalFilter } = useLocalDataTable(configs, columns)

const openDetails = (row: any) => {
  router.push(`/deep-research/configs/${row.id}`)
}

const onConfigCreated = (configId: string) => {
  router.push(`/deep-research/configs/${configId}`)
}
</script>
