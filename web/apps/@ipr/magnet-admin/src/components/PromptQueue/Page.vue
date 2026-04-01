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
    prompt-queue-create-new(:showNewDialog='showNewDialog', @cancel='showNewDialog = false', @created='onConfigCreated')
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { textColumn, chipCopyColumn, dateColumn } from '@/utils/columnHelpers'
import PromptQueueCreateNew from './CreateNew.vue'
import { usePromptQueueStore } from '@/stores/promptQueueStore'

const pqStore = usePromptQueueStore()
const router = useRouter()

const showNewDialog = ref(false)

const configs = computed(() => {
  const data = pqStore.promptQueueConfigs
  return Array.isArray(data) ? data : []
})

const columns = [
  textColumn('name', 'Name'),
  chipCopyColumn('System name'),
  textColumn('steps_count', 'Steps', {
    sortable: true,
    format: (val: unknown) => {
      // steps_count is computed from config.steps.length
      return val != null ? String(val) : '0'
    },
  }),
  dateColumn('created_at', 'Created'),
  dateColumn('updated_at', 'Last updated'),
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

<style lang="stylus" scoped>
.prompt-queue-container {
  min-width: 450px;
  max-width: 1200px;
  width: 100%;
}
</style>
