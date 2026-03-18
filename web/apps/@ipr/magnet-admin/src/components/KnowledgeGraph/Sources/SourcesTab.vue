<template>
  <div class="q-px-md">
    <div class="row items-start q-col-gutter-md q-mb-md">
      <div class="col">
        <div class="km-heading-7">Data Sources</div>
        <div class="km-description text-secondary-text">Manage document sources for this knowledge graph</div>
      </div>
    </div>

    <q-separator class="q-my-md" />

    <q-linear-progress v-if="loading" indeterminate color="primary" />

    <div v-else-if="displayRows.length === 0" class="q-mt-md">
      <div class="text-center q-pa-lg">
        <q-icon name="folder_open" size="64px" color="grey-5" />
        <div class="km-heading-7 text-grey-7 q-mt-md">No sources added yet</div>
        <div class="km-description text-grey-6">Start by uploading a file(s) or connecting to external data sources</div>
        <q-btn no-caps unelevated color="primary" label="Add First Source" class="q-mt-lg" @click="showSourceTypeDialog = true" />
      </div>
    </div>

    <div v-else>
      <kg-table-toolbar>
        <template #leading>
          <km-btn label="Sync All" size="sm" :disable="syncAllInProgress" @click="showSyncAllConfirmDialog = true" />
        </template>

        <template #trailing>
          <km-btn flat icon="o_add_circle" label="New Source" size="sm" @click="showSourceTypeDialog = true" />
          <km-btn flat icon="refresh" label="Refresh" size="sm" :disable="loading" @click="fetchSources(true)" />
        </template>
      </kg-table-toolbar>

      <q-table
        v-model:pagination="pagination"
        flat
        table-header-class="bg-primary-light"
        :rows="displayRows"
        :columns="columns"
        row-key="id"
        :rows-per-page-options="[10]"
        @row-click="onRowClick"
      >
        <template #body-cell-last_sync_at="slotScope">
          <q-td :props="slotScope">
            <div class="kg-sync-cell row items-center no-wrap">
              <!-- Status column (fixed width for alignment) -->
              <div class="column items-start justify-center q-gap-6">
                <kg-status-badge :status="effectiveStatus(slotScope.row)" />
                <div class="kg-sync-meta row items-center no-wrap q-gutter-x-xs q-ml-4">
                  <span class="kg-sync-meta-label">Last sync:</span>
                  <span class="kg-sync-meta-value">
                    {{ formatRelative(slotScope.row?.last_sync_at) }}
                    <q-tooltip anchor="top middle" self="bottom middle">
                      {{ formatFull(slotScope.row?.last_sync_at) }}
                    </q-tooltip>
                  </span>
                </div>
              </div>
            </div>
          </q-td>
        </template>
        <template #body-cell-schedule="slotScope">
          <q-td :props="slotScope">
            <div v-if="hasSchedule(slotScope.row)" class="column items-start justify-center q-gap-6">
              <div class="row items-center no-wrap q-gutter-x-xs">
                <q-icon name="schedule" color="primary" size="16px" />
                <span class="kg-sync-schedule-interval">{{ slotScope.row.schedule?.interval }}</span>
              </div>
              <div class="kg-sync-schedule-time">
                {{ formatScheduleSummary(slotScope.row.schedule) }}
              </div>
            </div>
            <div v-else class="text-grey-5 italic text-caption">Not scheduled</div>
          </q-td>
        </template>
        <template #body-cell-menu="slotScope">
          <q-td :props="slotScope" class="text-right">
            <q-btn dense flat color="dark" icon="more_vert" :disable="deletingIds.has(slotScope.row.id)" @click.stop>
              <q-menu class="kg-source-menu" anchor="bottom right" self="top right" auto-close>
                <q-list dense>
                  <q-item
                    v-ripple="false"
                    :disable="!isSyncable(slotScope.row.type) || syncingIds.has(slotScope.row.id)"
                    clickable
                    @click="handleSync(slotScope.row)"
                  >
                    <q-item-section thumbnail>
                      <q-icon name="sync" color="primary" size="20px" class="q-ml-sm" />
                    </q-item-section>
                    <q-item-section>Sync now</q-item-section>
                  </q-item>

                  <q-separator />

                  <q-item v-ripple="false" clickable @click="confirmPurge(slotScope.row)">
                    <q-item-section thumbnail>
                      <q-icon name="delete" color="negative" size="20px" class="q-ml-sm" />
                    </q-item-section>
                    <q-item-section>Delete data</q-item-section>
                  </q-item>

                  <q-item v-ripple="false" clickable @click="confirmDelete(slotScope.row)">
                    <q-item-section thumbnail>
                      <q-icon name="delete" color="negative" size="20px" class="q-ml-sm" />
                    </q-item-section>
                    <q-item-section>Delete source & data</q-item-section>
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
    <kg-confirm-dialog
      v-model="showDeleteDialog"
      title="Delete source"
      icon="delete_outline"
      :description="`Are you sure you want to delete '${selectedRow?.name}'?`"
      confirm-label="Delete"
      destructive
      :loading="deleteInProgress"
      @confirm="performDelete"
    >
      <template #warning>This will remove the source, its documents, and all chunks. This action cannot be undone.</template>
    </kg-confirm-dialog>

    <!-- Purge Source Data Dialog -->
    <kg-confirm-dialog
      v-model="showPurgeDialog"
      title="Purge all data"
      icon="delete_sweep"
      icon-variant="warning"
      :description="`Are you sure you want to purge all data from '${selectedRow?.name}'?`"
      confirm-label="Purge"
      destructive
      :loading="purgeInProgress"
      @confirm="performPurge"
    >
      <template #warning>
        This will delete all documents and chunks associated with this source. The source itself will be kept. This action cannot be undone.
      </template>
    </kg-confirm-dialog>

    <!-- Sync All Confirmation Dialog -->
    <kg-confirm-dialog
      v-model="showSyncAllConfirmDialog"
      title="Sync all sources"
      icon="sync"
      icon-variant="info"
      description="Are you sure you want to sync all sources? This will trigger a sync for every syncable source in this knowledge graph."
      confirm-label="Sync All"
      @confirm="onConfirmSyncAll"
    >
      <template #warning>Syncing may take a while depending on the number of sources and documents.</template>
    </kg-confirm-dialog>
  </div>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { formatRelative } from '@shared/utils'
import { QTableColumn, useQuasar } from 'quasar'
import { computed, inject, onMounted, ref, type Ref } from 'vue'
import { useStore } from 'vuex'
import { KgConfirmDialog, KgStatusBadge, KgTableToolbar } from '../common'
import { fetchKnowledgeGraphSources } from './api'
import { formatAdded, getSourceTypeName, type SourceRow, type SourceSchedule } from './models'
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
const showSyncAllConfirmDialog = ref(false)
const showDeleteDialog = ref(false)
const deleteInProgress = ref(false)
const showPurgeDialog = ref(false)
const purgeInProgress = ref(false)

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
    label: 'Sync Status',
    field: 'last_sync_at',
    format: formatAdded,
    align: 'left',
    sortable: true,
  },
  {
    name: 'schedule',
    label: 'Sync Schedule',
    field: 'schedule',
    align: 'left',
    sortable: false,
  },
  {
    name: 'menu',
    label: '',
    field: 'id',
  },
]

const fetchSources = async (force = false) => {
  loading.value = true
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    rows.value = await fetchKnowledgeGraphSources({
      endpoint,
      graphId: props.graphId,
      force,
    })

    // Keep selection in sync after refresh
    if (selectedRow.value) {
      selectedRow.value = rows.value.find((r) => r.id === selectedRow.value?.id) || null
    }
  } catch (error) {
    console.error('Error fetching sources:', error)
  } finally {
    loading.value = false
  }
}

function effectiveStatus(row: SourceRow): string {
  // If manual upload in progress, surface 'syncing' for upload source
  if ((kgUploading?.value && row.type === 'upload') || syncingIds.value.has(row.id)) {
    return 'syncing'
  }
  return (row.status || '').toLowerCase()
}

function hasSchedule(row: SourceRow): boolean {
  return !!row?.schedule
}

function toInt(value: unknown): number | null {
  if (value === null || value === undefined) return null
  const n = typeof value === 'number' ? value : Number.parseInt(String(value), 10)
  return Number.isFinite(n) ? n : null
}

function pad2(n: number): string {
  return String(n).padStart(2, '0')
}

function normalizeDayOfWeek(value: unknown): number | null {
  const n = toInt(value)
  if (n !== null && n >= 0 && n <= 6) return n

  const s = String(value || '')
    .toLowerCase()
    .trim()
  const map: Record<string, number> = {
    mon: 0,
    tue: 1,
    wed: 2,
    thu: 3,
    fri: 4,
    sat: 5,
    sun: 6,
  }
  return map[s] ?? null
}

function formatScheduleSummary(schedule?: SourceSchedule): string {
  if (!schedule) return ''
  const interval = String(schedule.interval || '').toLowerCase()
  const cron = schedule.cron || {}

  const cronHourRaw = (cron as any)?.hour
  if (interval === 'hourly' || String(cronHourRaw) === '*') return 'Every hour'

  const hour = toInt(cronHourRaw) ?? 3
  const minute = toInt((cron as any)?.minute) ?? 0
  const time = `${pad2(hour)}:${pad2(minute)}`

  const dayOfWeek = normalizeDayOfWeek((cron as any)?.day_of_week)
  const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

  if (interval === 'weekly' || dayOfWeek !== null) {
    const dayLabel = dayOfWeek !== null ? dayNames[dayOfWeek] : ''
    return dayLabel ? `Every ${dayLabel} at ${time}` : `Every day at ${time}`
  }

  return `Every day at ${time}`
}

const handleSourceTypeSelect = (sourceType: 'upload' | 'sharepoint' | 'fluid_topics' | 'salesforce') => {
  selectedRow.value = null
  activeSourceType.value = sourceType as SourceTypeKey
  sourceDialogOpen.value = true
}

const handleSourceCreated = () => {
  sourceDialogOpen.value = false
  selectedRow.value = null
  fetchSources(true)
  emit('refresh')
}

const handleSourceCancelled = () => {
  sourceDialogOpen.value = false
  selectedRow.value = null
}

const syncSource = async (source: SourceRow, showNotification = true): Promise<boolean> => {
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/sources/${source.id}/sync`,
      method: 'POST',
      credentials: 'include',
    })

    if (response.ok) {
      if (showNotification) {
        $q.notify({
          message: `Sync started for ${source.name}. Click Refresh to see progress.`,
          position: 'top',
          color: 'info',
          textColor: 'white',
          timeout: 2500,
        })
      }
      // Don't auto-refresh - user clicks Refresh button to see updated status
      return true
    } else {
      if (showNotification) {
        $q.notify({
          message: `Failed to start sync for ${source.name}`,
          position: 'top',
          color: 'error-text',
          timeout: 1000,
        })
      }
      return false
    }
  } catch (error) {
    console.error('Error syncing source:', error)
    if (showNotification) {
      $q.notify({
        type: 'negative',
        message: 'Error starting sync',
      })
    }
    return false
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
  await syncSource(source)
  // Fetch sources to show the "syncing" status from backend
  await fetchSources(true)
}

function onConfirmSyncAll() {
  showSyncAllConfirmDialog.value = false
  void handleSyncAll()
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
    let anySuccess = false
    let anyFailure = false
    for (const src of syncable) {
      const ok = await syncSource(src, false) // Don't show individual notifications
      anySuccess = anySuccess || ok
      anyFailure = anyFailure || !ok
    }
    // Fetch sources once after all syncs to show "syncing" status for all sources
    if (anySuccess) {
      await fetchSources(true)
    }
    // Show single notification for Sync All
    if (anySuccess && !anyFailure) {
      $q.notify({
        type: 'info',
        message: 'Sync started for all sources. Click Refresh to see progress.',
        position: 'top',
        textColor: 'white',
        timeout: 2500,
      })
    } else if (anySuccess && anyFailure) {
      $q.notify({ type: 'warning', message: 'Sync started with some errors', position: 'top', timeout: 2000 })
    } else {
      $q.notify({ type: 'negative', message: 'Failed to start sync', position: 'top', timeout: 2000 })
    }
  } finally {
    syncAllInProgress.value = false
  }
}

const activeDialogComponent = computed(() => {
  return activeSourceType.value ? getDialogComponentFor(activeSourceType.value) : null
})

const confirmDelete = (source: SourceRow) => {
  selectedRow.value = source
  showDeleteDialog.value = true
}

const performDelete = async () => {
  if (!selectedRow.value) return
  const source = selectedRow.value
  try {
    deleteInProgress.value = true
    deletingIds.value.add(source.id)
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/sources/${source.id}`,
      method: 'DELETE',
      credentials: 'include',
    })

    if (response.ok) {
      $q.notify({
        type: 'positive',
        message: 'Source and related content deleted',
        position: 'top',
        textColor: 'black',
        timeout: 1200,
      })
      showDeleteDialog.value = false
      fetchSources(true)
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

const confirmPurge = (source: SourceRow) => {
  selectedRow.value = source
  showPurgeDialog.value = true
}

const performPurge = async () => {
  if (!selectedRow.value) return
  const source = selectedRow.value
  try {
    purgeInProgress.value = true
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/sources/${source.id}/purge`,
      method: 'DELETE',
      credentials: 'include',
    })

    if (response.ok) {
      $q.notify({
        type: 'positive',
        message: 'Documents and chunks purged',
        position: 'top',
        textColor: 'black',
        timeout: 1200,
      })
      showPurgeDialog.value = false
      fetchSources(true)
      emit('refresh')
    } else {
      $q.notify({ type: 'negative', message: 'Failed to purge source data', position: 'top' })
    }
  } catch (error) {
    console.error('Error purging source data:', error)
    $q.notify({ type: 'negative', message: 'Error purging source data', position: 'top' })
  } finally {
    purgeInProgress.value = false
  }
}

const onRowClick = (evt: Event, row: SourceRow) => {
  selectedRow.value = row
  activeSourceType.value = (row.type as SourceTypeKey) || null
  sourceDialogOpen.value = true
}

defineExpose({
  refresh: () => fetchSources(true),
})

onMounted(() => {
  fetchSources()
})
</script>

<style scoped>
:deep(.q-table thead th) {
  font-size: 14px;
  font-weight: 600;
}

.kg-sync-meta {
  margin-top: 2px;
}

.kg-sync-meta-label {
  font-size: 12px;
  color: var(--q-secondary-text, rgba(0, 0, 0, 0.5));
}

.kg-sync-meta-value {
  font-size: 12px;
  color: var(--q-secondary-text, rgba(0, 0, 0, 0.75));
}

.kg-sync-schedule-interval {
  font-size: 13px;
  font-weight: 600;
  color: var(--q-primary);
  text-transform: capitalize;
}

.kg-sync-schedule-time {
  font-size: 12px;
  color: var(--q-secondary-text, rgba(0, 0, 0, 0.6));
}

/* Row menu: keep compact/default, without hover highlighting */
:deep(.kg-source-menu .q-focus-helper) {
  opacity: 0 !important;
}

:deep(.kg-source-menu .q-item.q-focusable:hover) {
  background: transparent !important;
}

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
</style>
