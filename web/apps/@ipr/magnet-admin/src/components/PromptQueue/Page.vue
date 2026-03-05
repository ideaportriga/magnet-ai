<template lang="pug">
.row.no-wrap.overflow-hidden.full-height
  q-scroll-area.fit
    .row.no-wrap.full-height.justify-center.fit
      .col-auto.prompt-queue-container
        .full-height.q-pb-md.relative-position.q-px-md
          .border.border-radius-12.bg-white.ba-border.q-my-16.q-pa-16.q-gap-16.full-width
            .row.q-mb-12
              .col-auto.center-flex-y
                km-input(placeholder='Search', iconBefore='search', v-model='searchString', @input='searchString = $event', clearable)
              q-space
              .col-auto.center-flex-y
                km-btn.q-mr-12(label='New', @click='showNewDialog = true')
            .row
              km-table(
                @selectRow='openDetails',
                selection='single',
                row-key='id',
                :selected='selectedConfig ? [selectedConfig] : []',
                :columns='columns',
                :rows='visibleRows',
                :visibleColumns='visibleColumns',
                style='min-width: 1100px',
                :loading='loading',
                binary-state-sort
              )
    prompt-queue-create-new(:showNewDialog='showNewDialog', @cancel='showNewDialog = false', @created='onConfigCreated')
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { ChipCopy } from '@ui'
import { markRaw } from 'vue'
import { formatDateTime } from '@shared/utils/dateTime'
import PromptQueueCreateNew from './CreateNew.vue'

const store = useStore()
const router = useRouter()

const searchString = ref('')
const showNewDialog = ref(false)
const selectedConfig = ref<any>(null)

const loading = computed(() => store.getters.promptQueueLoading)

const columns = [
  {
    name: 'name',
    label: 'Name',
    field: 'name',
    align: 'left' as const,
    sortable: true,
  },
  {
    name: 'system_name',
    label: 'System name',
    field: 'system_name',
    type: 'component',
    component: markRaw(ChipCopy),
    align: 'left' as const,
    sortable: true,
    classes: 'km-button-xs-text',
  },
  {
    name: 'steps_count',
    label: 'Steps',
    field: (row: any) => (row?.config?.steps?.length ?? 0),
    align: 'left' as const,
    sortable: true,
  },
  {
    name: 'created',
    label: 'Created',
    field: 'created_at',
    align: 'left' as const,
    sortable: true,
    format: (val: string) => formatDateTime(val),
    sort: (a: string, b: string) => {
      const dateA = new Date(a)
      const dateB = new Date(b)
      return dateA.getTime() - dateB.getTime()
    },
  },
  {
    name: 'last_updated',
    label: 'Last updated',
    field: 'updated_at',
    align: 'left' as const,
    sortable: true,
    format: (val: string) => formatDateTime(val),
    sort: (a: string, b: string) => {
      const dateA = new Date(a)
      const dateB = new Date(b)
      return dateA.getTime() - dateB.getTime()
    },
  },
]

const visibleColumns = computed(() => columns.map((c) => c.name))

const configs = computed(() => {
  const data = store.getters.promptQueueConfigs
  return Array.isArray(data) ? data : []
})

const visibleRows = computed(() => {
  let rows = configs.value
  if (searchString.value) {
    const search = searchString.value.toLowerCase()
    rows = rows.filter((item: any) => item.name?.toLowerCase().includes(search))
  }
  return rows
})

onMounted(async () => {
  await store.dispatch('fetchPromptQueueConfigs', true)
})

const openDetails = (row: any) => {
  selectedConfig.value = row
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
