<template lang="pug">
.row.no-wrap.overflow-hidden.full-height
  q-scroll-area.fit
    .row.no-wrap.full-height.justify-center.fit
      .col-auto.collection-container
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
                v-model:pagination='pagination',
                :loading='loading',
                binary-state-sort
              )
    deep-research-configs-create-new(:showNewDialog='showNewDialog', @cancel='showNewDialog = false', @created='onConfigCreated')
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { ChipCopy } from '@ui'
import { markRaw } from 'vue'
import { formatDateTime } from '@shared/utils/dateTime'
import DeepResearchCreateNew from './CreateNew.vue'

const store = useStore()
const router = useRouter()

const searchString = ref('')
const showNewDialog = ref(false)
const selectedConfig = ref<any>(null)
const loading = ref(false)

const pagination = ref({
  rowsPerPage: 10,
  page: 1,
  sortBy: 'name',
  descending: false,
  rowsNumber: 0,
})

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

const visibleColumns = computed(() => columns.map(c => c.name))

const configs = computed(() => {
  const configsData = store.getters.configs
  return Array.isArray(configsData) ? configsData : []
})

const visibleRows = computed(() => {
  let rows = configs.value

  if (searchString.value) {
    const search = searchString.value.toLowerCase()
    rows = rows.filter((item: any) => {
      return item.name?.toLowerCase().includes(search)
    })
  }

  return rows
})

onMounted(async () => {
  // Data is already loaded in App.vue on initialization
  // No need to fetch again
})

const openDetails = (row: any) => {
  selectedConfig.value = row
  router.push(`/deep-research/configs/${row.id}`)
}

const onConfigCreated = (configId: string) => {
  router.push(`/deep-research/configs/${configId}`)
}
</script>

<style lang="stylus">
.collection-container {
  min-width: 450px;
  max-width: 1200px;
  width: 100%;
}
</style>
