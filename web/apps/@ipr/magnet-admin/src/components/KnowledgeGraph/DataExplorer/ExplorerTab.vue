<template>
  <div class="row no-wrap full-height">
    <div class="col q-px-md">
      <div class="row items-center q-mb-md">
        <div class="col">
          <div class="km-heading-7">Data Explorer</div>
          <div class="km-description text-secondary-text">Browse documents and chunks in this knowledge graph</div>
        </div>
        <div class="col-auto row items-center q-gutter-md">
          <!-- View Mode Toggle -->
          <q-btn-toggle
            v-model="viewMode"
            toggle-color="primary"
            :options="[
              { label: 'Documents', value: 'documents' },
              { label: 'Chunks', value: 'chunks' },
            ]"
            unelevated
            no-caps
            size="sm"
          />
          <!-- Search -->
          <km-input v-model="searchQuery" placeholder="Search..." icon-before="search" clearable style="width: 250px" />
        </div>
      </div>

      <q-separator class="q-my-md" />

      <q-linear-progress v-if="loading" indeterminate color="primary" />

      <!-- Documents View -->
      <div v-if="viewMode === 'documents' && !loading">
        <div v-if="filteredDocuments.length === 0" class="q-mt-md">
          <div class="text-center q-pa-lg">
            <q-icon name="description" size="64px" color="grey-5" />
            <div class="km-heading-7 text-grey-7 q-mt-md">No documents found</div>
            <div class="km-description text-grey-6">
              {{ searchQuery ? 'Try a different search query' : 'Add sources to start populating this graph' }}
            </div>
          </div>
        </div>

        <q-table
          v-else
          v-model:pagination="documentsPagination"
          flat
          table-header-class="bg-primary-light"
          :rows="filteredDocuments"
          :columns="documentsColumns"
          row-key="id"
          :loading="loading"
          :rows-per-page-options="[10]"
          @row-click="onDocumentClick"
        >
          <template #body-cell-menu="slotScope">
            <q-td :props="slotScope" class="flex items-center justify-end q-gap-2">
              <km-btn
                flat
                color="secondary-text"
                label-class="km-button-text"
                icon-size="16px"
                icon="fa fa-external-link"
                :disable="!slotScope.row.external_link"
                @click.stop="openExternalLink(slotScope.row.external_link)"
              />
              <q-btn dense flat color="dark" icon="more_vert" :disable="deletingIds.has(slotScope.row.id)" @click.stop>
                <q-menu anchor="bottom right" self="top right" auto-close>
                  <q-list dense>
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
          <template #body-cell-name="slotScope">
            <q-td :props="slotScope">
              <div class="row items-center no-wrap q-gutter-x-sm">
                <kg-file-type-badge :type="slotScope.row.type" />
                <div style="max-width: 300px">
                  <div class="text-body2 text-weight-medium ellipsis">
                    {{ slotScope.row.title }}
                    <q-tooltip>{{ slotScope.row.title }}</q-tooltip>
                  </div>
                  <div class="text-caption text-grey-6 ellipsis">
                    {{ slotScope.row.name || '—' }}
                    <q-tooltip v-if="slotScope.row.name">{{ slotScope.row.name }}</q-tooltip>
                  </div>
                </div>
              </div>
            </q-td>
          </template>
          <template #body-cell-status="slotScope">
            <q-td :props="slotScope">
              <kg-status-badge :status="slotScope.row.status" :message="slotScope.row.status_message" />
            </q-td>
          </template>
        </q-table>
      </div>

      <!-- Chunks View -->
      <div v-if="viewMode === 'chunks' && !loading">
        <div v-if="filteredChunks.length === 0" class="q-mt-md">
          <div class="text-center q-pa-lg">
            <q-icon name="article" size="64px" color="grey-5" />
            <div class="km-heading-7 text-grey-7 q-mt-md">No chunks found</div>
            <div class="km-description text-grey-6">
              {{ searchQuery ? 'Try a different search query' : 'No chunks available in this graph' }}
            </div>
          </div>
        </div>

        <q-table
          v-else
          v-model:pagination="chunksPagination"
          flat
          table-header-class="bg-primary-light"
          :rows="filteredChunks"
          :columns="chunksColumns"
          row-key="id"
          :loading="loading"
          :rows-per-page-options="[5]"
          @request="onChunksRequest"
          @row-click="onChunkClick"
        >
          <template #body-cell-title="slotScope">
            <q-td :props="slotScope">
              <div class="row items-center no-wrap q-gutter-x-sm">
                <kg-chunk-type-badge v-if="slotScope.row.chunk_type" :type="slotScope.row.chunk_type" />
                <div>
                  <div class="text-body2 text-weight-medium">
                    {{ slotScope.row.title || slotScope.row.name || '—' }}
                  </div>
                  <div class="text-caption text-grey-6">
                    {{ slotScope.row.name || '—' }}
                  </div>
                </div>
              </div>
            </q-td>
          </template>
        </q-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { formatDuration, formatRelative } from '@shared/utils'
import { QTableColumn, useQuasar } from 'quasar'
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { KgChunkTypeBadge, KgFileTypeBadge, KgStatusBadge } from '../common'
import { Chunk, Document } from './models'

const props = defineProps<{
  graphId: string
  graphDetails: Record<string, any>
}>()

const emit = defineEmits<{
  (e: 'selectChunk', value: Chunk): void
}>()

const router = useRouter()
const store = useStore()

const documents = ref<Document[]>([])
const deletingIds = ref<Set<string>>(new Set())
const chunks = ref<Chunk[]>([])
const searchQuery = ref('')
const loading = ref(false)
const viewMode = ref<'documents' | 'chunks'>('documents')

const documentsPagination = ref({ rowsPerPage: 10, page: 1 })
const chunksPagination = ref({
  page: 1,
  rowsPerPage: 10,
  rowsNumber: 0,
})

const documentsColumns: QTableColumn<Document>[] = [
  {
    name: 'name',
    label: 'Document',
    field: 'name',
    align: 'left',
    sortable: true,
  },
  {
    name: 'source_name',
    label: 'Source',
    field: 'source_name',
    align: 'left',
    sortable: true,
  },
  {
    name: 'content_profile',
    label: 'Profile',
    field: 'content_profile',
    align: 'left',
    sortable: true,
  },
  {
    name: 'chunks_count',
    label: 'Chunks',
    field: 'chunks_count',
    format: (val) => val || 0,
    align: 'right',
    sortable: true,
  },
  {
    name: 'status',
    label: 'Status',
    field: 'status',
    align: 'left',
    sortable: true,
  },
  {
    name: 'processing_time',
    label: 'Processing Time',
    field: 'processing_time',
    format: (val) => formatDuration(val && val * 1000),
    align: 'right',
    sortable: true,
  },
  {
    name: 'updated_at',
    label: 'Updated',
    field: 'updated_at',
    format: formatRelative,
    align: 'left',
    sortable: true,
  },
  {
    name: 'created_at',
    label: 'Created',
    field: 'created_at',
    format: formatRelative,
    align: 'left',
    sortable: true,
  },
  {
    name: 'menu',
    label: '',
    field: 'id',
  },
]
const chunksColumns: QTableColumn<Chunk>[] = [
  {
    name: 'title',
    label: 'Chunk',
    field: 'title',
    align: 'left',
  },
  {
    name: 'document_name',
    label: 'Document',
    field: 'document_name',
    align: 'left',
  },
]

const filteredDocuments = computed(() => {
  if (!searchQuery.value) return documents.value
  const search = searchQuery.value.toLowerCase()
  return documents.value.filter(
    (doc) =>
      doc.name?.toLowerCase().includes(search) || doc.description?.toLowerCase().includes(search) || doc.source_name?.toLowerCase().includes(search)
  )
})

const filteredChunks = computed(() => {
  // Server-side filtering via API
  return chunks.value
})

const fetchDocuments = async () => {
  loading.value = true
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/documents`,
      method: 'GET',
      credentials: 'include',
    })

    if (response.ok) {
      documents.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching documents:', error)
  } finally {
    loading.value = false
  }
}

const fetchChunks = async (page = 1, rowsPerPage = 20, search = '') => {
  loading.value = true
  try {
    const offset = (page - 1) * rowsPerPage
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const searchParam = search ? `&q=${encodeURIComponent(search)}` : ''
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/chunks?limit=${rowsPerPage}&offset=${offset}${searchParam}`,
      method: 'GET',
      credentials: 'include',
    })

    if (response.ok) {
      const data = await response.json()
      chunks.value = data.chunks || []
      chunksPagination.value.rowsNumber = data.total || 0
    }
  } catch (error) {
    console.error('Error fetching chunks:', error)
  } finally {
    loading.value = false
  }
}

const onDocumentClick = (evt: Event, row: Document) => {
  router.push(`/knowledge-graph/${props.graphId}/documents/${row.id}`)
}

const onChunkClick = (evt: Event, row: Chunk) => {
  emit('selectChunk', row)
}

const onChunksRequest = (props: any) => {
  const { page, rowsPerPage } = props.pagination
  chunksPagination.value.page = page
  chunksPagination.value.rowsPerPage = rowsPerPage
  fetchChunks(page, rowsPerPage, searchQuery.value)
}

// Quasar instance for dialogs
const $q = useQuasar()

const confirmDelete = (row: Document) => {
  // Confirm then call delete
  void $q
    .dialog({
      title: 'Delete document',
      message: `Are you sure you want to delete "${row.title || row.name}"? This cannot be undone.`,
      cancel: true,
      persistent: true,
      ok: {
        color: 'negative',
        label: 'Delete',
        flat: true,
      },
    })
    .onOk(async () => {
      try {
        deletingIds.value.add(row.id)
        const endpoint = store.getters.config.api.aiBridge.urlAdmin
        const response = await fetchData({
          endpoint,
          service: `knowledge_graphs/${props.graphId}/documents/${row.id}`,
          method: 'DELETE',
          credentials: 'include',
        })
        if (response.ok) {
          // Remove from list immediately and refresh
          documents.value = documents.value.filter((d) => d.id !== row.id)
        }
      } catch (e) {
        console.error('Failed to delete document', e)
      } finally {
        deletingIds.value.delete(row.id)
      }
    })
}

const openExternalLink = (url?: string) => {
  const target = (url || '').trim()
  if (!target) return
  window.open(target, '_blank', 'noopener')
}

// Watch for view mode changes
watch(viewMode, (newMode) => {
  if (newMode === 'documents' && documents.value.length === 0) {
    fetchDocuments()
  } else if (newMode === 'chunks' && chunks.value.length === 0) {
    fetchChunks(chunksPagination.value.page, chunksPagination.value.rowsPerPage, searchQuery.value)
  }
})

// Watch for search query changes in chunks mode
watch(searchQuery, (newQuery) => {
  if (viewMode.value === 'chunks') {
    // Reset to first page when searching
    chunksPagination.value.page = 1
    fetchChunks(1, chunksPagination.value.rowsPerPage, newQuery)
  }
})

onMounted(() => {
  fetchDocuments()
})

// Expose refresh method so parent can trigger reloads after uploads
defineExpose({
  refresh: () => {
    if (viewMode.value === 'documents') {
      fetchDocuments()
    } else {
      fetchChunks(chunksPagination.value.page, chunksPagination.value.rowsPerPage, searchQuery.value)
    }
  },
})
</script>

<style scoped>
:deep(.q-table thead th) {
  font-size: 14px;
  font-weight: 600;
}

:deep(.q-table tbody td) {
  height: 47px;
}

:deep(.q-table tbody td) {
  padding: 3px 16px;
}

:deep(tr:hover .row-actions) {
  opacity: 1;
  pointer-events: auto;
}

:deep(.row-actions) {
  display: inline-flex;
  gap: 4px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s ease;
}
</style>
