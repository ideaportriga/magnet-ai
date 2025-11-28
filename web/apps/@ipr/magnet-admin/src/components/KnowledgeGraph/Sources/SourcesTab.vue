<template>
  <div class="q-px-md">
    <div class="row items-center q-mb-md">
      <div class="col">
        <div class="km-heading-7">Data Sources</div>
        <div class="km-description text-secondary-text">Manage document sources for this knowledge graph</div>
      </div>
      <div class="col-auto">
        <div class="row items-center no-wrap q-gutter-x-sm">
          <km-btn label="Sync All" size="sm" @click="handleSyncAll" />
          <km-btn label="New" size="sm" @click="showSourceTypeDialog = true" />
        </div>
      </div>
    </div>

    <q-separator class="q-my-md" />

    <q-linear-progress v-if="loading" indeterminate color="primary" />

    <div v-else-if="displayRows.length === 0" class="q-mt-md">
      <div class="text-center q-pa-lg">
        <q-icon name="folder_open" size="64px" color="grey-5" />
        <div class="km-heading-7 text-grey-7 q-mt-md">No sources added yet</div>
        <div class="km-description text-grey-6">Start by uploading a file(s) or connecting to external data sources</div>
      </div>
    </div>

    <div v-else class="q-mt-md">
      <q-table
        v-model:pagination="pagination"
        flat
        table-header-class="bg-primary-light"
        :rows="displayRows"
        :columns="columns"
        row-key="id"
        :loading="loading"
        :rows-per-page-options="[10]"
        @row-click="onRowClick"
      >
        <template #body-cell-last_sync_at="slotScope">
          <q-td :props="slotScope">
            <div class="column items-start justify-center q-gutter-y-xs">
              <div class="row items-center no-wrap q-gutter-x-sm">
                <q-chip
                  :class="['text-uppercase q-ma-none', { 'chip-rotating': effectiveStatus(slotScope.row) === 'syncing' }]"
                  size="sm"
                  :color="getSourceStatusColor(effectiveStatus(slotScope.row))"
                  :text-color="getSourceStatusTextColor(effectiveStatus(slotScope.row))"
                  :label="formatSourceStatusLabel(effectiveStatus(slotScope.row))"
                  :icon="getSourceStatusIcon(effectiveStatus(slotScope.row))"
                />
              </div>
              <div class="row items-center no-wrap">
                <span class="text-caption">
                  {{ formatRelative(slotScope.row?.last_sync_at) }}
                </span>
                <q-tooltip anchor="top middle" self="bottom middle">
                  {{ formatFull(slotScope.row?.last_sync_at) }}
                </q-tooltip>
              </div>
            </div>
          </q-td>
        </template>
        <template #body-cell-menu="slotScope">
          <q-td :props="slotScope" class="text-right">
            <q-btn dense flat color="dark" icon="more_vert" :disable="deletingIds.has(slotScope.row.id)" @click.stop>
              <q-menu anchor="bottom right" self="top right" auto-close>
                <q-list dense>
                  <q-item :disable="slotScope.row.type === 'upload' || syncingIds.has(slotScope.row.id)" clickable @click="handleSync(slotScope.row)">
                    <q-item-section thumbnail>
                      <q-icon name="sync" color="primary" size="20px" class="q-ml-sm" />
                    </q-item-section>
                    <q-item-section>Sync now</q-item-section>
                  </q-item>
                  <q-item :disable="slotScope.row.type === 'upload'" clickable @click="configureAutoSync(slotScope.row)">
                    <q-item-section thumbnail>
                      <q-icon name="schedule" size="20px" class="q-ml-sm" />
                    </q-item-section>
                    <q-item-section>Sync schedule</q-item-section>
                  </q-item>
                  <q-separator />
                  <q-item clickable @click="confirmDelete(slotScope.row)">
                    <q-item-section thumbnail>
                      <q-icon name="delete" color="negative" size="20px" class="q-ml-sm" />
                    </q-item-section>
                    <q-item-section>Delete</q-item-section>
                  </q-item>
                </q-list>
              </q-menu>
            </q-btn>
          </q-td>
        </template>
      </q-table>
    </div>

    <!-- Source Type Selection Dialog -->
    <source-type-dialog
      :show-dialog="showSourceTypeDialog"
      @update:show-dialog="showSourceTypeDialog = $event"
      @select="handleSourceTypeSelect"
      @cancel="showSourceTypeDialog = false"
    />

    <component
      :is="activeDialogComponent"
      v-if="sourceDialogOpen && activeSourceType"
      :show-dialog="sourceDialogOpen"
      :graph-id="graphId"
      :source="selectedRow"
      @update:show-dialog="(v: boolean) => (sourceDialogOpen = v)"
      @cancel="handleSourceCancelled"
      @created="handleSourceCreated"
    />

    <!-- Delete Source Dialog -->
    <q-dialog v-model="showDeleteDialog">
      <q-card data-test="popup-confirm" class="column" style="width: 676px; height: 370px; padding: 32px">
        <q-card-section class="card-section-style">
          <div class="row">
            <div class="col">
              <div class="km-heading-7">Delete source</div>
            </div>
            <div class="col-auto">
              <q-btn icon="close" flat dense @click="showDeleteDialog = false" />
            </div>
          </div>
        </q-card-section>
        <q-card-section class="card-section-style q-mb-md">
          <div class="km-description text-secondary-text">
            <span class="text-weight-medium">Choose how you want to delete {{ selectedRow?.name }}.</span>
          </div>
        </q-card-section>
        <q-card-section class="card-section-style">
          <q-option-group v-model="deleteMode" type="radio" :options="deleteOptions" />
        </q-card-section>
        <q-card-section v-if="deleteMode === 'cascade_all'" class="card-section-style">
          <div
            class="km-description q-mt-lg row items-center q-gap-8 q-pa-md rounded-borders bg-yellow-1 text-yellow-10"
            style="border: 1px solid var(--q-warning)"
          >
            <q-icon name="warning" color="yellow-8" size="26px" />
            <div class="col">This will remove the source, its documents, and all chunks. This action cannot be undone.</div>
          </div>
        </q-card-section>
        <q-card-actions class="dialog-actions">
          <div class="col-auto">
            <km-btn flat :label="'Cancel'" color="primary" @click="showDeleteDialog = false" />
          </div>
          <div class="col" />
          <div class="col-auto">
            <km-btn
              :label="deleteMode === 'cascade_all' ? 'Delete All' : 'Delete Source'"
              :data-test="deleteMode === 'cascade_all' ? 'Delete All' : 'Delete Source'"
              bg="error-bg"
              hover-bg="error-text"
              color="error-text"
              @click="performDelete"
            />
          </div>
        </q-card-actions>
        <q-inner-loading :showing="deleteInProgress" />
      </q-card>
    </q-dialog>
  </div>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { formatRelative } from '@shared/utils'
import { QTableColumn, useQuasar } from 'quasar'
import { computed, inject, onMounted, ref, type Ref } from 'vue'
import { useStore } from 'vuex'
import { formatAdded, getSourceTypeName, SourceRow } from './models'
import SourceTypeDialog from './SourceTypeDialog.vue'
import { getDialogComponentFor, isSyncable, type SourceTypeKey } from './SourceTypes/registry'

const props = defineProps<{
  graphId: string
  graphDetails: Record<string, any>
}>()

const emit = defineEmits<{
  refresh: []
}>()

const store = useStore()
const $q = useQuasar()

const loading = ref(false)
const showSourceTypeDialog = ref(false)
const activeSourceType = ref<SourceTypeKey | null>(null)
const sourceDialogOpen = ref(false)

const rows = ref<SourceRow[]>([])
const selectedRow = ref<SourceRow | null>(null)
const pagination = ref({ rowsPerPage: 10, page: 1 })
const deletingIds = ref<Set<string>>(new Set())
const syncingIds = ref<Set<string>>(new Set())
const syncAllInProgress = ref(false)
const showDeleteDialog = ref(false)
const deleteMode = ref<'source_only' | 'cascade_all'>('source_only')
const deleteInProgress = ref(false)
const deleteOptions = [
  {
    label: 'Delete source only',
    value: 'source_only',
    description: 'Keep documents and chunks; they remain in the graph.',
  },
  {
    label: 'Delete source, documents and chunks',
    value: 'cascade_all',
    description: 'Remove everything associated with this source.',
  },
]

// Inject global uploading flag to reflect 'syncing' for upload source immediately
const kgUploading = inject<Ref<boolean>>('kgUploading')

const displayRows = computed(() => {
  const hasUploadSource = rows.value.some((r) => r.type === 'upload')
  if (kgUploading?.value && !hasUploadSource) {
    // Inject a temporary row for immediate feedback
    const tempRow: SourceRow = {
      id: 'temp-upload-source',
      name: 'Manual Upload',
      type: 'upload',
      status: 'syncing', // will trigger spinner
      created_at: new Date().toISOString(),
      documents_count: 0,
      last_sync_at: undefined,
    }
    return [tempRow, ...rows.value]
  }
  return rows.value
})

const columns: QTableColumn<SourceRow>[] = [
  {
    name: 'name',
    label: 'Name',
    field: 'name',
    align: 'left',
    sortable: true,
  },
  {
    name: 'type',
    label: 'Type',
    field: 'type',
    format: getSourceTypeName,
    align: 'left',
    sortable: true,
  },
  {
    name: 'documents_count',
    label: 'Documents',
    field: 'documents_count',
    align: 'left',
    sortable: true,
  },
  {
    name: 'created_at',
    label: 'Added',
    field: 'created_at',
    format: formatAdded,
    align: 'left',
    sortable: true,
  },
  {
    name: 'last_sync_at',
    label: 'Last Sync',
    field: 'last_sync_at',
    format: formatAdded,
    align: 'left',
    sortable: true,
  },
  {
    name: 'menu',
    label: '',
    field: 'id',
  },
]

const fetchSources = async () => {
  loading.value = true
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs//${props.graphId}/sources`,
      method: 'GET',
      credentials: 'include',
    })

    if (response.ok) {
      rows.value = await response.json()
      // Keep selection in sync after refresh
      if (selectedRow.value) {
        selectedRow.value = rows.value.find((r) => r.id === selectedRow.value?.id) || null
      }
    }
  } catch (error) {
    console.error('Error fetching sources:', error)
  } finally {
    loading.value = false
  }
}

function formatSourceStatusLabel(status?: string) {
  const s = (status || '').toLowerCase()
  if (!s) return 'unknown'
  return s.split('_').join(' ')
}

function effectiveStatus(row: SourceRow): string {
  // If manual upload in progress, surface 'syncing' for upload source
  if ((kgUploading?.value && row.type === 'upload') || syncingIds.value.has(row.id)) {
    return 'syncing'
  }
  return (row.status || '').toLowerCase()
}

function getSourceStatusColor(status?: string) {
  switch ((status || '').toLowerCase()) {
    case 'completed':
      return 'status-ready'
    case 'syncing':
      return 'info'
    case 'partial':
      return 'warning'
    case 'failed':
    case 'error':
      return 'error-bg'
    case 'not_synced':
      return 'gray'
    default:
      return 'gray'
  }
}

function getSourceStatusTextColor(status?: string) {
  switch ((status || '').toLowerCase()) {
    case 'completed':
      return 'status-ready-text'
    case 'syncing':
      return 'white'
    case 'partial':
      return 'black'
    case 'failed':
    case 'error':
      return 'error-text'
    case 'not_synced':
      return 'text-gray'
    default:
      return 'text-gray'
  }
}

function getSourceStatusIcon(status?: string) {
  switch ((status || '').toLowerCase()) {
    case 'completed':
      return 'check_circle'
    case 'syncing':
      return 'sync'
    case 'partial':
      return 'warning'
    case 'failed':
    case 'error':
      return 'error'
    case 'not_synced':
      return 'schedule'
    default:
      return 'help_outline'
  }
}

const handleSourceTypeSelect = (sourceType: 'upload' | 'sharepoint' | 'fluid_topics') => {
  selectedRow.value = null
  activeSourceType.value = sourceType as SourceTypeKey
  sourceDialogOpen.value = true
}

const handleSourceCreated = () => {
  sourceDialogOpen.value = false
  selectedRow.value = null
  fetchSources()
  emit('refresh')
}

const handleSourceCancelled = () => {
  sourceDialogOpen.value = false
  selectedRow.value = null
}

const syncSource = async (source: SourceRow) => {
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs//${props.graphId}/sources/${source.id}/sync`,
      method: 'POST',
      credentials: 'include',
    })

    if (response.ok) {
      $q.notify({
        message: `Source ${source.name} synchronized successfully`,
        position: 'top',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })
      fetchSources()
    } else {
      $q.notify({
        message: `Failed to synchronize source ${source.name}`,
        position: 'top',
        color: 'error-text',
        timeout: 1000,
      })
    }
  } catch (error) {
    console.error('Error syncing source:', error)
    $q.notify({
      type: 'negative',
      message: 'Error syncing SharePoint',
    })
  } finally {
    $q.loading.hide()
  }
}

function formatFull(dateStr?: string) {
  if (!dateStr) return 'Never'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString()
  } catch {
    return '—'
  }
}

const handleSync = async (source: SourceRow) => {
  try {
    syncingIds.value.add(source.id)
    await syncSource(source)
  } finally {
    syncingIds.value.delete(source.id)
  }
}

const handleSyncAll = async () => {
  if (!rows.value?.length) {
    $q.notify({ type: 'info', message: 'No sources to sync', position: 'top', timeout: 1000 })
    return
  }
  syncAllInProgress.value = true
  try {
    const syncable = rows.value.filter((r) => isSyncable(r.type))
    if (syncable.length === 0) {
      $q.notify({ type: 'info', message: 'No syncable sources found', position: 'top', timeout: 1000 })
      return
    }
    for (const src of syncable) {
      try {
        syncingIds.value.add(src.id)
        await syncSource(src)
      } finally {
        syncingIds.value.delete(src.id)
      }
    }
    $q.notify({ type: 'positive', message: 'Sync complete', position: 'top', textColor: 'black', timeout: 1000 })
  } finally {
    syncAllInProgress.value = false
  }
}

const activeDialogComponent = computed(() => {
  return activeSourceType.value ? getDialogComponentFor(activeSourceType.value) : null
})

const configureAutoSync = (_source: SourceRow) => {
  $q.notify({
    type: 'warning',
    message: 'Sync job configuration is not yet implemented.',
    position: 'top',
    timeout: 1500,
  })
}

const confirmDelete = (source: SourceRow) => {
  selectedRow.value = source
  deleteMode.value = 'source_only'
  showDeleteDialog.value = true
}

const performDelete = async () => {
  if (!selectedRow.value) return
  const source = selectedRow.value
  try {
    deleteInProgress.value = true
    deletingIds.value.add(source.id)
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const cascade = deleteMode.value === 'cascade_all'
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs//${props.graphId}/sources/${source.id}?cascade=${cascade ? 'true' : 'false'}`,
      method: 'DELETE',
      credentials: 'include',
    })

    if (response.ok) {
      $q.notify({
        type: 'positive',
        message: cascade ? 'Source and related content deleted' : 'Source deleted',
        position: 'top',
        textColor: 'black',
        timeout: 1200,
      })
      showDeleteDialog.value = false
      fetchSources()
      emit('refresh')
    } else {
      $q.notify({ type: 'negative', message: 'Failed to delete source', position: 'top' })
    }
  } catch (error) {
    console.error('Error deleting source:', error)
    $q.notify({ type: 'negative', message: 'Error deleting source', position: 'top' })
  } finally {
    deleteInProgress.value = false
    deletingIds.value.delete(selectedRow.value.id)
  }
}

const onRowClick = (evt: Event, row: SourceRow) => {
  selectedRow.value = row
  activeSourceType.value = (row.type as SourceTypeKey) || null
  sourceDialogOpen.value = true
}

defineExpose({
  refresh: () => fetchSources(),
})

onMounted(() => {
  fetchSources()
})
</script>

<style scoped>
@keyframes chip-rotate {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

:deep(.chip-rotating .q-chip__icon) {
  animation: chip-rotate 1s linear infinite;
}

.card-section-style {
  padding: 0 !important;
}

.dialog-actions {
  margin-top: auto;
  padding: 30px 0 0 0 !important;
}
</style>
