<template>
  <div class="q-px-md">
    <div class="row items-start q-col-gutter-md q-mb-md">
      <div class="col">
        <div class="km-heading-7">{{ m.knowledgeGraph_dataSources() }}</div>
        <div class="km-description text-secondary-text">{{ m.knowledgeGraph_dataSourcesDesc() }}</div>
      </div>
    </div>

    <q-separator class="q-my-md" />

    <q-linear-progress v-if="loading" indeterminate color="primary" />

    <div v-else-if="displayRows.length === 0" class="q-mt-md">
      <div class="text-center q-pa-lg">
        <q-icon name="folder_open" size="64px" color="grey-5" />
        <div class="km-heading-7 text-grey-7 q-mt-md">{{ m.knowledgeGraph_noSourcesAdded() }}</div>
        <div class="km-description text-grey-6">{{ m.knowledgeGraph_addFirstSourceHint() }}</div>
        <q-btn no-caps unelevated color="primary" :label="m.knowledgeGraph_addFirstSource()" class="q-mt-lg" @click="showSourceTypeDialog = true" />
      </div>
    </div>

    <div v-else>
      <kg-table-toolbar>
        <template #leading>
          <km-btn :label="m.knowledgeGraph_syncAll()" size="sm" :disable="syncAllInProgress" @click="showSyncAllConfirmDialog = true" />
        </template>

        <template #trailing>
          <km-btn flat icon="o_add_circle" :label="m.knowledgeGraph_newSource()" size="sm" @click="showSourceTypeDialog = true" />
          <km-btn flat icon="refresh" :label="m.common_refresh()" size="sm" :disable="loading" @click="fetchSources(true)" />
        </template>
      </kg-table-toolbar>

      <!-- §E.2.5 — km-data-table migration. Status/schedule/menu cells use
           named slots; primitive cells (name, documents_count, created_at)
           fall through to FlexRender on the column's default cell. -->
      <km-data-table
        :table="table"
        row-key="id"
        :loading="loading"
        hide-pagination
        @row-click="onRowClick"
      >
        <template #cell-type="{ row }">
          {{ getSourceTypeName(row.type) }}
        </template>

        <template #cell-created_at="{ row }">
          {{ formatAdded(row.created_at) }}
        </template>

        <template #cell-last_sync_at="{ row }">
          <div class="kg-sync-cell row items-center no-wrap">
            <div class="column items-start justify-center q-gap-6">
              <kg-status-badge :status="effectiveStatus(row)" />
              <div class="kg-sync-meta row items-center no-wrap q-gutter-x-xs q-ml-4">
                <span class="kg-sync-meta-label">{{ m.knowledgeGraph_lastSync() }}</span>
                <span class="kg-sync-meta-value">
                  {{ formatRelative(row?.last_sync_at) }}
                  <q-tooltip anchor="top middle" self="bottom middle">
                    {{ formatFull(row?.last_sync_at) }}
                  </q-tooltip>
                </span>
              </div>
            </div>
          </div>
        </template>

        <template #cell-schedule="{ row }">
          <div v-if="hasSchedule(row)" class="column items-start justify-center q-gap-6">
            <div class="row items-center no-wrap q-gutter-x-xs">
              <q-icon name="schedule" color="primary" size="16px" />
              <span class="kg-sync-schedule-interval">{{ row.schedule?.interval }}</span>
            </div>
            <div class="kg-sync-schedule-time">
              {{ formatScheduleSummary(row.schedule) }}
            </div>
          </div>
          <div v-else class="text-grey-5 italic text-caption">{{ m.knowledgeGraph_notScheduled() }}</div>
        </template>

        <template #cell-menu="{ row }">
          <q-btn dense flat color="dark" icon="more_vert" :disable="deletingIds.has(row.id)" @click.stop>
            <q-menu class="kg-source-menu" anchor="bottom right" self="top right" auto-close>
              <q-list dense>
                <q-item
                  v-ripple="false"
                  :disable="!isSyncable(row.type) || syncingIds.has(row.id)"
                  clickable
                  @click="handleSync(row)"
                >
                  <q-item-section thumbnail>
                    <q-icon name="sync" color="primary" size="20px" class="q-ml-sm" />
                  </q-item-section>
                  <q-item-section>{{ m.knowledgeGraph_syncNow() }}</q-item-section>
                </q-item>

                <q-separator />

                <q-item v-ripple="false" clickable @click="confirmPurge(row)">
                  <q-item-section thumbnail>
                    <q-icon name="delete" color="negative" size="20px" class="q-ml-sm" />
                  </q-item-section>
                  <q-item-section>{{ m.knowledgeGraph_deleteData() }}</q-item-section>
                </q-item>

                <q-item v-ripple="false" clickable @click="confirmDelete(row)">
                  <q-item-section thumbnail>
                    <q-icon name="delete" color="negative" size="20px" class="q-ml-sm" />
                  </q-item-section>
                  <q-item-section>{{ m.knowledgeGraph_deleteSourceAndData() }}</q-item-section>
                </q-item>
              </q-list>
            </q-menu>
          </q-btn>
        </template>
      </km-data-table>
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
      :title="m.knowledgeGraph_deleteSourceTitle()"
      icon="delete_outline"
      :description="m.knowledgeGraph_deleteSourceDesc({ name: selectedRow?.name || '' })"
      :confirm-label="m.common_delete()"
      destructive
      :loading="deleteInProgress"
      @confirm="performDelete"
    >
      <template #warning>{{ m.knowledgeGraph_deleteSourceWarning() }}</template>
    </kg-confirm-dialog>

    <!-- Purge Source Data Dialog -->
    <kg-confirm-dialog
      v-model="showPurgeDialog"
      :title="m.knowledgeGraph_purgeAllData()"
      icon="delete_sweep"
      icon-variant="warning"
      :description="m.knowledgeGraph_purgeSourceDesc({ name: selectedRow?.name || '' })"
      :confirm-label="m.knowledgeGraph_purge()"
      destructive
      :loading="purgeInProgress"
      @confirm="performPurge"
    >
      <template #warning>{{ m.knowledgeGraph_purgeWarning() }}</template>
    </kg-confirm-dialog>

    <!-- Sync All Confirmation Dialog -->
    <kg-confirm-dialog
      v-model="showSyncAllConfirmDialog"
      :title="m.knowledgeGraph_syncAllTitle()"
      icon="sync"
      icon-variant="info"
      :description="m.knowledgeGraph_syncAllDesc()"
      :confirm-label="m.knowledgeGraph_syncAll()"
      @confirm="onConfirmSyncAll"
    >
      <template #warning>{{ m.knowledgeGraph_syncAllWarning() }}</template>
    </kg-confirm-dialog>
  </div>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { m } from '@/paraglide/messages'
import { formatRelative } from '@shared/utils'
import { useQuasar } from 'quasar'
import type { ColumnDef } from '@tanstack/vue-table'
import { computed, inject, onMounted, ref, type Ref } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { useNotify } from '@/composables/useNotify'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { KgConfirmDialog, KgStatusBadge, KgTableToolbar } from '../common'
import type { KnowledgeGraphDetails } from '../types'
import { fetchKnowledgeGraphSources } from './api'
import { formatAdded, getSourceTypeName, type SourceRow, type SourceSchedule } from './models'
import SourceTypeDialog from './SourceTypeDialog.vue'
import { getDialogComponentFor, isSyncable, type SourceTypeKey } from './SourceTypes/registry'

const props = defineProps<{
  graphId: string
  graphDetails: KnowledgeGraphDetails
}>()

const emit = defineEmits<{
  refresh: []
}>()

const appStore = useAppStore()
const $q = useQuasar()
const { notifySuccess, notifyError, notifyWarning, notifyInfo } = useNotify()

const loading = ref(false)
const showSourceTypeDialog = ref(false)
const activeSourceType = ref<SourceTypeKey | null>(null)
const sourceDialogOpen = ref(false)

const rows = ref<SourceRow[]>([])
const selectedRow = ref<SourceRow | null>(null)
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
      name: m.knowledgeGraph_manualUpload(),
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

// §E.2.5 — TanStack columns. Cell rendering delegated to named slots above
// for non-trivial ones; primitive columns use accessorKey.
const columns: ColumnDef<SourceRow, unknown>[] = [
  {
    id: 'name',
    accessorKey: 'name',
    header: m.knowledgeGraph_colName(),
    enableSorting: true,
    meta: { align: 'left' },
  },
  {
    id: 'type',
    accessorKey: 'type',
    header: m.knowledgeGraph_colType(),
    enableSorting: true,
    meta: { align: 'left' },
  },
  {
    id: 'documents_count',
    accessorKey: 'documents_count',
    header: m.knowledgeGraph_colDocuments(),
    enableSorting: true,
    meta: { align: 'left' },
  },
  {
    id: 'created_at',
    accessorKey: 'created_at',
    header: m.knowledgeGraph_colAdded(),
    enableSorting: true,
    meta: { align: 'left' },
  },
  {
    id: 'last_sync_at',
    accessorKey: 'last_sync_at',
    header: m.knowledgeGraph_colSyncStatus(),
    enableSorting: true,
    meta: { align: 'left' },
  },
  {
    id: 'schedule',
    header: m.knowledgeGraph_colSyncSchedule(),
    enableSorting: false,
    meta: { align: 'left' },
  },
  {
    id: 'menu',
    header: '',
    enableSorting: false,
    meta: { align: 'right', width: '60px' },
  },
]

const { table } = useLocalDataTable<SourceRow>(displayRows, columns, {
  defaultPageSize: 100,
})

const fetchSources = async (force = false) => {
  loading.value = true
  try {
    const endpoint = appStore.config.api.aiBridge.urlAdmin
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
    const endpoint = appStore.config.api.aiBridge.urlAdmin
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/sources/${source.id}/sync`,
      method: 'POST',
      credentials: 'include',
    })

    if (response.ok) {
      if (showNotification) {
        notifyInfo(m.knowledgeGraph_syncStarted({ name: source.name }))
      }
      // Don't auto-refresh - user clicks Refresh button to see updated status
      return true
    } else {
      if (showNotification) {
        notifyError(m.knowledgeGraph_syncFailed({ name: source.name }))
      }
      return false
    }
  } catch (error) {

    if (showNotification) {
      notifyError(m.knowledgeGraph_syncError())
    }
    return false
  } finally {
    $q.loading.hide()
  }
}

function formatFull(dateStr?: string) {
  if (!dateStr) return m.knowledgeGraph_neverSynced()
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
    notifyInfo(m.knowledgeGraph_noSources())
    return
  }
  syncAllInProgress.value = true
  try {
    const syncable = rows.value.filter((r) => isSyncable(r.type))
    if (syncable.length === 0) {
      notifyInfo(m.knowledgeGraph_noSyncableSources())
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
      notifyInfo(m.knowledgeGraph_syncAllStarted())
    } else if (anySuccess && anyFailure) {
      notifyWarning(m.knowledgeGraph_syncAllPartial())
    } else {
      notifyError(m.knowledgeGraph_syncAllFailed())
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
    const endpoint = appStore.config.api.aiBridge.urlAdmin
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/sources/${source.id}`,
      method: 'DELETE',
      credentials: 'include',
    })

    if (response.ok) {
      notifySuccess(m.knowledgeGraph_sourceDeleted())
      showDeleteDialog.value = false
      fetchSources(true)
      emit('refresh')
    } else {
      notifyError(m.knowledgeGraph_deleteFailed())
    }
  } catch (error) {

    notifyError(m.knowledgeGraph_deleteError())
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
    const endpoint = appStore.config.api.aiBridge.urlAdmin
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/sources/${source.id}/purge`,
      method: 'DELETE',
      credentials: 'include',
    })

    if (response.ok) {
      notifySuccess(m.knowledgeGraph_dataPurged())
      showPurgeDialog.value = false
      fetchSources(true)
      emit('refresh')
    } else {
      notifyError(m.knowledgeGraph_purgeFailed())
    }
  } catch (error) {

    notifyError(m.knowledgeGraph_purgeError())
  } finally {
    purgeInProgress.value = false
  }
}

const onRowClick = (row: SourceRow) => {
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
  font-size: var(--km-body-sm-size, 14px);
  font-weight: 600;
}

.kg-sync-meta {
  margin-top: 2px;
}

.kg-sync-meta-label {
  font-size: var(--km-caption-size, 12px);
  color: var(--q-secondary-text);
}

.kg-sync-meta-value {
  font-size: var(--km-caption-size, 12px);
  color: var(--q-secondary-text);
}

.kg-sync-schedule-interval {
  font-size: var(--km-body-sm-size, 13px);
  font-weight: 600;
  color: var(--q-primary);
  text-transform: capitalize;
}

.kg-sync-schedule-time {
  font-size: var(--km-caption-size, 12px);
  color: var(--q-secondary-text);
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
