<template lang="pug">
.column.no-wrap.full-height
  q-scroll-area.fit
    .col-auto.collection-container.q-mx-auto.full-width.q-px-md.q-pt-16

      //- Stats cards
      .row.q-gap-16.q-mb-16(v-if="stats")
        .col
          .border.border-radius-12.bg-white.ba-border.q-pa-16
            .text-caption.text-grey-7 Total files
            .text-h6 {{ stats.total_files }}
            .text-caption.text-grey-7 {{ formatBytes(stats.total_size) }}
        .col(v-for="item in stats.by_entity_type", :key="item.entity_type")
          .border.border-radius-12.bg-white.ba-border.q-pa-16
            .text-caption.text-grey-7 {{ item.entity_type }}
            .text-h6 {{ item.count }}
            .text-caption.text-grey-7 {{ formatBytes(item.total_size) }}

      //- Backend breakdown
      .row.q-gap-16.q-mb-16(v-if="stats && stats.by_backend.length > 1")
        .col(v-for="item in stats.by_backend", :key="item.backend_key")
          .border.border-radius-12.bg-white.ba-border.q-pa-12
            .row.items-center.q-gap-8
              q-icon(name="fas fa-hard-drive", size="16px", color="grey-7")
              .text-caption.text-grey-7 {{ item.backend_key }}
              q-space
              .text-body2 {{ item.count }} files
              .text-caption.text-grey-7.q-ml-8 {{ formatBytes(item.total_size) }}

      //- Files table
      .ba-border.border-radius-12.bg-white.q-pa-16.column(style="min-height: 0")
        .row.q-mb-12.items-center
          km-input.q-mr-12(placeholder="Search", iconBefore="search", :modelValue="globalFilter", @input="globalFilter = $event", clearable)
          q-select.q-mr-12(
            v-model="filterEntityType",
            :options="entityTypeOptions",
            label="Entity type",
            clearable,
            dense,
            outlined,
            emit-value,
            map-options,
            style="min-width: 180px"
          )
          q-select(
            v-model="filterBackend",
            :options="backendOptions",
            label="Backend",
            clearable,
            dense,
            outlined,
            emit-value,
            map-options,
            style="min-width: 160px"
          )
          q-space
          km-btn(
            icon="refresh",
            label="Refresh",
            @click="onRefresh",
            iconColor="icon",
            hoverColor="primary",
            labelClass="km-title",
            flat,
            iconSize="16px",
            hoverBg="primary-bg"
          )
        .col(style="min-height: 0")
          km-data-table(:table="table", :loading="isLoading", fill-height, row-key="id")
            template(#cell-filename="{ row }")
              a.cursor-pointer.text-primary(@click.prevent="downloadFile(row)") {{ row.filename }}
            template(#cell-size="{ row }")
              | {{ formatBytes(row.size) }}
            template(#cell-created_at="{ row }")
              | {{ formatDate(row.created_at) }}
            template(#cell-expires_at="{ row }")
              template(v-if="row.expires_at")
                q-badge(:color="isExpiringSoon(row.expires_at) ? 'orange-7' : 'grey-6'", text-color="white")
                  | {{ formatTTL(row.expires_at) }}
            template(#cell-actions="{ row }")
              .row.no-wrap.items-center.justify-end
                km-btn(
                  icon="download",
                  flat,
                  dense,
                  size="sm",
                  iconSize="14px",
                  iconColor="icon",
                  hoverColor="primary",
                  hoverBg="primary-bg",
                  tooltip="Download",
                  @click.stop="downloadFile(row)"
                )
                km-btn(
                  icon="delete",
                  flat,
                  dense,
                  size="sm",
                  iconSize="14px",
                  iconColor="icon",
                  hoverColor="negative",
                  hoverBg="negative-bg",
                  tooltip="Delete",
                  @click.stop="confirmDelete(row)"
                )

  //- Delete confirmation dialog
  q-dialog(v-model="showDeleteDialog")
    q-card(style="min-width: 350px")
      q-card-section
        .text-h6 Delete file
      q-card-section.q-pt-none
        | Are you sure you want to delete&nbsp;
        strong {{ fileToDelete?.filename }}
        | ?
      q-card-actions(align="right")
        q-btn(flat, label="Cancel", @click="showDeleteDialog = false")
        q-btn(flat, label="Delete", color="negative", @click="deleteFile")
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { DateTime } from 'luxon'
import { fetchData } from '@shared'
import { useDataTable } from '@/composables/useDataTable'
import { textColumn, dateColumn } from '@/utils/columnHelpers'
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
  textColumn<StoredFile>('filename', 'Filename'),
  textColumn<StoredFile>('size', 'Size', { align: 'right' }),
  textColumn<StoredFile>('entity_type', 'Entity type'),
  dateColumn<StoredFile>('created_at', 'Created'),
  {
    id: 'expires_at',
    accessorKey: 'expires_at',
    header: 'Expires',
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

const { table, isLoading, globalFilter, refetch } = useDataTable<StoredFile>('files', columns, {
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
    notifyError(`Download failed: ${e.message || e}`)
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
  const m = Math.floor(diff.minutes % 60)
  if (h < 0 || (h === 0 && m < 0)) return 'expired'
  if (h === 0) return `${m}m`
  return `${h}h ${m}m`
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

<style lang="stylus" scoped>
.collection-container
  min-width 450px
  max-width 1200px
  width 100%
  overflow hidden
</style>
