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
          fill-height,
          :table='table',
          row-key='id',
          @row-click='openDetails'
        )
    deep-research-configs-create-new(:showNewDialog='showNewDialog', @cancel='showNewDialog = false', @created='onConfigCreated')
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
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
  textColumn('name', 'Name'),
  chipCopyColumn('System name'),
  dateColumn('created_at', 'Created'),
  dateColumn('updated_at', 'Last updated'),
]

const { table, globalFilter } = useLocalDataTable(configs, columns)

const openDetails = (row: any) => {
  router.push(`/deep-research/configs/${row.id}`)
}

const onConfigCreated = (configId: string) => {
  router.push(`/deep-research/configs/${configId}`)
}
</script>
