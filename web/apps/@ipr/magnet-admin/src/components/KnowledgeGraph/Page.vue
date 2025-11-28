<template>
  <div class="row no-wrap overflow-hidden full-height">
    <q-scroll-area class="fit">
      <div class="row no-wrap full-height justify-center fit">
        <div class="col-auto knowledge-graph-container">
          <div class="full-height q-pb-md relative-position q-px-md">
            <div class="border border-radius-12 bg-white ba-border q-my-16 q-pa-16 q-gap-16 full-width">
              <div class="row q-mb-12">
                <div class="col-auto center-flex-y">
                  <km-input v-model="searchString" placeholder="Search" icon-before="search" clearable @input="searchString = $event" />
                </div>
                <q-space />
                <div class="col-auto center-flex-y">
                  <km-btn class="q-mr-12" label="New" @click="showCreateDialog = true" />
                </div>
              </div>
              <div class="row">
                <km-table
                  ref="table"
                  row-key="id"
                  :columns="columns"
                  :rows="visibleRows ?? []"
                  style="min-width: 1100px"
                  :pagination="pagination"
                  @select-row="openDetails"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </q-scroll-area>
  </div>

  <create-graph-dialog v-if="showCreateDialog" :show-dialog="showCreateDialog" @cancel="showCreateDialog = false" @created="handleGraphCreated" />
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import CreateGraphDialog from './CreateGraphDialog.vue'

const router = useRouter()
const store = useStore()
const items = ref<any[]>([])
const searchString = ref('')
const showCreateDialog = ref(false)
const loading = ref(false)

const columns = [
  {
    name: 'name',
    label: 'Name',
    field: 'name',
    align: 'left',
    sortable: true,
  },
  {
    name: 'documents_count',
    label: 'Documents',
    field: 'documents_count',
    align: 'right',
    sortable: true,
  },
  {
    name: 'chunks_count',
    label: 'Chunks',
    field: 'chunks_count',
    align: 'right',
    sortable: true,
  },
  {
    name: 'created_at',
    label: 'Created',
    field: 'created_at',
    align: 'left',
    sortable: true,
    format: (val: string) => (val ? new Date(val).toLocaleString() : ''),
  },
]

const visibleRows = computed(() => {
  if (!searchString.value) return items.value
  const search = searchString.value.toLowerCase()
  return items.value.filter((item) => item.name?.toLowerCase().includes(search) || item.system_name?.toLowerCase().includes(search))
})

const pagination = ref({
  rowsPerPage: 50,
})

const fetchGraphs = async () => {
  loading.value = true
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const response = await fetchData({
      endpoint,
      service: 'knowledge_graphs/',
      method: 'GET',
      credentials: 'include',
    })

    if (response.ok) {
      const data = await response.json()
      items.value = data
    }
  } catch (error) {
    console.error('Error fetching knowledge graphs:', error)
  } finally {
    loading.value = false
  }
}

const openDetails = (row: any) => {
  router.push(`/knowledge-graph/${row.id}`)
}

const handleGraphCreated = (result: any) => {
  showCreateDialog.value = false
  fetchGraphs()
  if (result?.id) {
    router.push(`/knowledge-graph/${result.id}`)
  }
}

onMounted(() => {
  fetchGraphs()
})
</script>

<style scoped>
.knowledge-graph-container {
  min-width: 450px;
  max-width: 1200px;
  width: 100%;
}
</style>
