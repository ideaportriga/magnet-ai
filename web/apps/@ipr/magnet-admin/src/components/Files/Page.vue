<template>
  <div class="stack full-height" data-gap="0">
    <km-scroll-area class="fit">
      <div class="flex-none collection-container mx-auto full-width px-md pt-lg">
        <div v-if="stats" class="cluster mb-lg" data-gap="lg">
          <div class="flex-1">
            <div class="border border-radius-12 bg-white ba-border p-lg">
              <div class="text-caption text-grey-7">{{ m.files_totalFiles() }}</div>
              <div class="text-h6">{{ stats.total_files }}</div>
              <div class="text-caption text-grey-7">{{ formatBytes(stats.total_size) }}</div>
            </div>
          </div>
          <div v-for="item in stats.by_entity_type" :key="item.entity_type" class="flex-1">
            <div class="border border-radius-12 bg-white ba-border p-lg">
              <div class="text-caption text-grey-7">{{ item.entity_type }}</div>
              <div class="text-h6">{{ item.count }}</div>
              <div class="text-caption text-grey-7">{{ formatBytes(item.total_size) }}</div>
            </div>
          </div>
        </div>
        <div v-if="stats &amp;&amp; stats.by_backend.length &gt; 1" class="cluster mb-lg" data-gap="lg">
          <div v-for="item in stats.by_backend" :key="item.backend_key" class="flex-1">
            <div class="border border-radius-12 bg-white ba-border p-md">
              <div class="cluster" data-gap="sm">
                <km-glyph name="storage" size="16px" tone="weak" />
                <div class="text-caption text-grey-7">{{ item.backend_key }}</div>
                <div class="km-space" />
                <div class="text-body2">{{ m.files_filesCount({ count: String(item.count) }) }}</div>
                <div class="text-caption text-grey-7 ml-sm">{{ formatBytes(item.total_size) }}</div>
              </div>
            </div>
          </div>
        </div>
        <div class="ba-border border-radius-12 bg-white p-lg stack" data-gap="0" style="min-block-size: 0">
          <div class="cluster mb-md">
            <km-input class="mr-md" :placeholder="m.common_search()" icon-before="search" :model-value="globalFilter" clearable @input="globalFilter = $event" />
            <km-select v-model="filterEntityType" class="mr-md" :options="entityTypeOptions" :label="m.files_entityType()" clearable dense outlined emit-value map-options style="min-inline-size: 180px" />
            <km-select v-model="filterBackend" :options="backendOptions" :label="m.files_backend()" clearable dense outlined emit-value map-options style="min-inline-size: 160px" />
            <div class="km-space" />
            <km-btn icon="refresh" :label="m.common_refresh()" interaction-tone="brand" label-class="km-title" flat icon-size="16px" @click="onRefresh" />
          </div>
          <div class="flex-1" style="min-block-size: 0">
            <km-data-table :table="table" :loading="isLoading" fill-height row-key="id">
              <template #cell-filename="{ row }"><a class="cursor-pointer text-primary" @click.prevent="downloadFile(row)">{{ row.filename }}</a></template>
              <template #cell-size="{ row }">{{ formatBytes(row.size) }}</template>
              <template #cell-created_at="{ row }">{{ formatDate(row.created_at) }}</template>
              <template #cell-expires_at="{ row }">
                <template v-if="row.expires_at">
                  <km-badge :tone="isExpiringSoon(row.expires_at) ? 'warning' : 'neutral'">{{ formatTTL(row.expires_at) }}</km-badge>
                </template>
              </template>
              <template #cell-actions="{ row }">
                <div class="cluster" data-wrap="no" data-justify="end">
                  <km-btn icon="download" flat dense size="sm" icon-size="14px" interaction-tone="brand" :tooltip="m.common_download()" @click.stop="downloadFile(row)" />
                  <km-btn icon="delete" flat dense size="sm" icon-size="14px" interaction-tone="danger" :tooltip="m.common_delete()" @click.stop="confirmDelete(row)" />
                </div>
              </template>
            </km-data-table>
          </div>
        </div>
      </div>
    </km-scroll-area>
    <km-dialog v-model="showDeleteDialog">
      <km-card style="min-inline-size: 350px">
        <div class="km-card-section">
          <div class="text-h6">{{ m.files_deleteFile() }}</div>
        </div>
        <div class="km-card-section pt-0">{{ m.files_deleteFileConfirm() }}&nbsp;<strong>{{ fileToDelete?.filename }}</strong>?</div>
        <div class="km-card-actions" align="right">
          <km-btn flat :label="m.common_cancel()" @click="showDeleteDialog = false" />
          <km-btn flat :label="m.common_delete()" tone="danger" @click="deleteFile" />
        </div>
      </km-card>
    </km-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { DateTime } from 'luxon'
import { fetchData } from '@shared'
import { useDataTable } from '@/composables/useDataTable'
import { textColumn, dateColumn } from '@/utils/columnHelpers'
import { m } from '@/paraglide/messages'
import { useAppStore } from '@/stores/appStore'
import { useEntityQueries } from '@/queries/entities'
import { useNotify } from '@/composables/useNotify'
import type { StoredFile } from '@/types'

const { notifySuccess, notifyError } = useNotify()
const appStore = useAppStore()
const queries = useEntityQueries()
const endpoint = computed(() => appStore.config?.api?.aiBridge?.urlAdmin)
const credentials = computed(() => appStore.config?.auth?.enabled ? 'include' : null)

// Filters
const filterEntityType = ref<string | null>(null)
const filterBackend = ref<string | null>(null)

// Stats (separate endpoint, not part of standard entity pattern)
const stats = ref<any>(null)

const entityTypeOptions = computed(() => {
  if (!stats.value?.by_entity_type) return []
  return stats.value.by_entity_type.map((i: any) => ({
    label: `${i.entity_type} (${i.count})`,
    value: i.entity_type,
  }))
})

const backendOptions = computed(() => {
  if (!stats.value?.by_backend) return []
  return stats.value.by_backend.map((i: any) => ({
    label: `${i.backend_key} (${i.count})`,
    value: i.backend_key,
  }))
})

// Extra params for useDataTable (filters passed as query params)
const extraParams = computed(() => {
  const params: Record<string, unknown> = {}
  if (filterEntityType.value) params.entity_type = filterEntityType.value
  if (filterBackend.value) params.backend_key = filterBackend.value
  return params
})

// Table columns
const columns = [
  textColumn<StoredFile>('filename', m.files_filename()),
  textColumn<StoredFile>('size', m.files_size(), { align: 'right' }),
  textColumn<StoredFile>('entity_type', m.files_entityType()),
  dateColumn<StoredFile>('created_at', m.common_created()),
  {
    id: 'expires_at',
    accessorKey: 'expires_at',
    header: m.files_expires(),
    enableSorting: false,
    meta: { align: 'left' as const },
  },
  {
    id: 'actions',
    accessorFn: () => null,
    header: '',
    enableSorting: false,
    meta: { align: 'right' as const },
  },
]

const { table, isLoading, isFetching, globalFilter, refetch } = useDataTable<StoredFile>('files', columns, {
  defaultSort: [{ id: 'created_at', desc: true }],
  defaultPageSize: 50,
  extraParams,
})

// Stats loading
async function loadStats() {
  if (!endpoint.value) return
  const res = await fetchData({
    endpoint: endpoint.value,
    service: 'files/stats',
    credentials: credentials.value,
  })
  if (res.ok) {
    stats.value = await res.json()
  }
}

function onRefresh() {
  refetch()
  loadStats()
}

// Download / Delete
const showDeleteDialog = ref(false)
const fileToDelete = ref<StoredFile | null>(null)

async function downloadFile(row: StoredFile) {
  try {
    const res = await fetchData({
      endpoint: endpoint.value,
      service: `files/${row.id}/download`,
      credentials: credentials.value,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || err.error || `HTTP ${res.status}`)
    }
    const blob = await res.blob()
    const objectUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = objectUrl
    a.download = row.filename || 'download'
    a.click()
    URL.revokeObjectURL(objectUrl)
  } catch (e: any) {
    notifyError(m.files_downloadFailed({ error: e.message || String(e) }))
  }
}

function confirmDelete(row: StoredFile) {
  fileToDelete.value = row
  showDeleteDialog.value = true
}

const removeMutation = queries.files.useRemove()

async function deleteFile() {
  if (!fileToDelete.value?.id) return
  removeMutation.mutate(fileToDelete.value.id, {
    onSuccess: () => {
      showDeleteDialog.value = false
      fileToDelete.value = null
      loadStats()
    },
  })
}

// Formatters
function formatBytes(bytes: number | undefined) {
  if (!bytes || bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0)} ${units[i]}`
}

function formatDate(isoStr: string | undefined) {
  if (!isoStr) return ''
  return DateTime.fromISO(isoStr).toFormat('LL/dd/yyyy HH:mm')
}

function formatTTL(isoStr: string) {
  if (!isoStr) return ''
  const diff = DateTime.fromISO(isoStr).diffNow(['hours', 'minutes'])
  const h = Math.floor(diff.hours)
  const mins = Math.floor(diff.minutes % 60)
  if (h < 0 || (h === 0 && mins < 0)) return m.files_expired()
  if (h === 0) return `${mins}m`
  return `${h}h ${mins}m`
}

function isExpiringSoon(isoStr: string) {
  if (!isoStr) return false
  const diff = DateTime.fromISO(isoStr).diffNow('hours').hours
  return diff < 2
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.collection-container {
  min-inline-size: 450px;
  max-inline-size: 1200px;
  inline-size: 100%;
  overflow: hidden;
}
</style>
