<template>
  <div class="row no-wrap full-height">
    <div class="col q-px-md">
      <div class="row items-center q-mb-md">
        <div class="col">
          <div class="km-heading-7">Data Explorer</div>
          <div class="km-description text-secondary-text">Browse documents, chunks and extracted entities in this knowledge graph</div>
        </div>
        <div class="col-auto row items-center q-gutter-md">
          <div class="view-mode-toggle">
            <div class="view-mode-toggle__track">
              <div class="view-mode-toggle__indicator" :class="{ 'view-mode-toggle__indicator--right': viewMode === 'entities' }" />
              <button
                class="view-mode-toggle__btn"
                :class="{ 'view-mode-toggle__btn--active': viewMode === 'documents' }"
                @click="viewMode = 'documents'"
              >
                <span class="view-mode-toggle__icon">
                  <q-icon name="description" size="18px" />
                </span>
                <span class="view-mode-toggle__label">Documents</span>
                <span class="view-mode-toggle__icon-spacer" aria-hidden="true" />
              </button>
              <button
                class="view-mode-toggle__btn"
                :class="{ 'view-mode-toggle__btn--active': viewMode === 'entities' }"
                @click="viewMode = 'entities'"
              >
                <span class="view-mode-toggle__icon">
                  <q-icon name="hub" size="18px" />
                </span>
                <span class="view-mode-toggle__label">Entities</span>
                <span class="view-mode-toggle__icon-spacer" aria-hidden="true" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <q-separator class="q-my-md" />

      <kg-table-toolbar v-if="hasRecords || loading">
        <template #leading>
          <q-btn v-if="viewMode === 'entities' && selectedEntityType" flat dense icon="arrow_back" @click="clearSelectedEntityType" />
          <div v-if="viewMode === 'entities' && selectedEntityType" class="km-heading-8">{{ selectedEntityType }}</div>
          <km-input v-if="hasRecords" v-model="searchQuery" placeholder="Search..." icon-before="search" clearable class="search-input" />
        </template>

        <template #trailing>
          <km-btn flat icon="refresh" label="Refresh" size="sm" @click="refresh" />
        </template>
      </kg-table-toolbar>

      <q-linear-progress v-if="loading" indeterminate color="primary" />

      <div v-if="!loading && !hasRecords" class="text-center q-pa-lg">
        <q-icon :name="viewMode === 'documents' ? 'description' : 'hub'" size="64px" color="grey-5" />
        <div class="km-heading-7 text-grey-7 q-mt-md">
          {{ viewMode === 'documents' ? 'No documents yet' : 'No entities yet' }}
        </div>
        <div class="km-description text-grey-6 q-mb-md">
          {{
            viewMode === 'documents' ? 'Upload documents to this knowledge graph to get started.' : 'Run entity extraction to populate entities here.'
          }}
        </div>
        <q-btn no-caps unelevated color="primary" label="Refresh" @click="refresh" />
      </div>

      <div v-if="!loading && hasRecords && viewMode === 'documents' && filteredDocuments.length === 0" class="text-center q-pa-lg">
        <div class="km-description text-grey-6">Try a different search query</div>
      </div>

      <div v-if="!loading && viewMode === 'entities' && selectedEntityType && entityRecords.length === 0" class="text-center q-pa-lg">
        <div class="km-description text-grey-6">No extracted records for this entity type yet</div>
      </div>

      <documents-table
        v-if="viewMode === 'documents' && !loading && filteredDocuments.length > 0"
        :documents="filteredDocuments"
        :deleting-ids="deletingIds"
        @document-click="onDocumentClick"
        @delete-document="confirmDelete"
        @open-external-link="openExternalLink"
      />

      <entities-table
        v-if="viewMode === 'entities' && !loading && entityTypes.length > 0"
        v-model:entity-records-pagination="entityRecordsPagination"
        :graph-details="graphDetails"
        :entity-types="entityTypes"
        :selected-entity-type="selectedEntityType"
        :entity-records="entityRecords"
        :deleting-entity-types="deletingEntityTypes"
        :deleting-entity-record-ids="deletingEntityRecordIds"
        @select-entity-type="onEntityTypeClick"
        @request-entity-records="onEntityRecordsRequest"
        @delete-entity-type="confirmDeleteEntityType"
        @delete-entity-record="confirmDeleteEntityRecord"
      />
    </div>

    <!-- Delete Document Dialog -->
    <kg-confirm-dialog
      v-model="showDeleteDialog"
      title="Delete document"
      icon="delete_outline"
      :description="`Are you sure you want to delete '${deletingDocument?.title || deletingDocument?.name}'?`"
      confirm-label="Delete"
      destructive
      :loading="deleteInProgress"
      @confirm="performDelete"
    />

    <!-- Delete Entity Record Dialog -->
    <kg-confirm-dialog
      v-model="showDeleteEntityRecordDialog"
      title="Delete entity record"
      icon="delete_outline"
      :description="`Are you sure you want to delete entity '${deletingEntityRecord?.record_identifier}'?`"
      confirm-label="Delete"
      destructive
      :loading="deleteEntityRecordInProgress"
      @confirm="performDeleteEntityRecord"
    />

    <!-- Delete Entity Type Dialog -->
    <kg-confirm-dialog
      v-model="showDeleteEntityTypeDialog"
      title="Delete all records"
      icon="delete_outline"
      :description="`Are you sure you want to delete all ${deletingEntityType?.count || 0} records of '${deletingEntityType?.entity}'?`"
      confirm-label="Delete All"
      destructive
      :loading="deleteEntityTypeInProgress"
      @confirm="performDeleteEntityType"
    />
  </div>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/appStore'
import { useNotify } from '@/composables/useNotify'
import { KgConfirmDialog, KgTableToolbar } from '../common'
import DocumentsTable from './DocumentsTable.vue'
import EntitiesTable from './EntitiesTable.vue'
import type { Document, EntityRecord, EntityTypeSummary } from './models'

const props = defineProps<{
  graphId: string
  graphDetails: Record<string, unknown>
}>()

const { notifyError } = useNotify()
const router = useRouter()
const appStore = useAppStore()

const documents = ref<Document[]>([])
const deletingIds = ref<Set<string>>(new Set())
const searchQuery = ref('')
const loading = ref(false)
const viewMode = ref<'documents' | 'entities'>('documents')

const entityTypes = ref<EntityTypeSummary[]>([])
const selectedEntityType = ref<string | null>(null)
const entityRecords = ref<EntityRecord[]>([])
const entityRecordsPagination = ref({
  page: 1,
  rowsPerPage: 10,
  rowsNumber: 0,
})

type EntityRecordsRequest = {
  pagination: {
    page: number
    rowsPerPage: number
  }
}

const hasRecords = computed(() => {
  if (viewMode.value === 'documents') return documents.value.length > 0
  return entityTypes.value.length > 0
})

const filteredDocuments = computed(() => {
  if (!searchQuery.value) return documents.value
  const search = searchQuery.value.toLowerCase()
  return documents.value.filter(
    (doc) =>
      doc.name?.toLowerCase().includes(search) || doc.description?.toLowerCase().includes(search) || doc.source_name?.toLowerCase().includes(search)
  )
})

const fetchDocuments = async () => {
  loading.value = true
  try {
    const endpoint = appStore.config.api.aiBridge.urlAdmin
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
    notifyError('Failed to load documents. Please try again.')
  } finally {
    loading.value = false
  }
}

const fetchEntityTypes = async () => {
  loading.value = true
  try {
    const endpoint = appStore.config.api.aiBridge.urlAdmin
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/entities`,
      method: 'GET',
      credentials: 'include',
    })
    if (response.ok) {
      entityTypes.value = await response.json()
    } else {
      entityTypes.value = []
    }
  } catch (error) {

    entityTypes.value = []
  } finally {
    loading.value = false
  }
}

const fetchEntityRecords = async (entity: string, page = 1, rowsPerPage = 10) => {
  loading.value = true
  try {
    const offset = (page - 1) * rowsPerPage
    const endpoint = appStore.config.api.aiBridge.urlAdmin
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/entities/records?entity=${encodeURIComponent(entity)}&limit=${rowsPerPage}&offset=${offset}`,
      method: 'GET',
      credentials: 'include',
    })
    if (response.ok) {
      const data = await response.json()
      entityRecords.value = data.records || []
      entityRecordsPagination.value.rowsNumber = data.total || 0
    } else {
      entityRecords.value = []
      entityRecordsPagination.value.rowsNumber = 0
    }
  } catch (error) {

    entityRecords.value = []
    entityRecordsPagination.value.rowsNumber = 0
  } finally {
    loading.value = false
  }
}

const onEntityTypeClick = (row: EntityTypeSummary) => {
  selectedEntityType.value = row.entity
  entityRecordsPagination.value.page = 1
  fetchEntityRecords(row.entity, 1, entityRecordsPagination.value.rowsPerPage)
}

const onEntityRecordsRequest = (reqProps: EntityRecordsRequest) => {
  const { page, rowsPerPage } = reqProps.pagination
  entityRecordsPagination.value.page = page
  entityRecordsPagination.value.rowsPerPage = rowsPerPage
  if (selectedEntityType.value) {
    fetchEntityRecords(selectedEntityType.value, page, rowsPerPage)
  }
}

const onDocumentClick = (row: Document) => {
  router.push(`/knowledge-graph/${props.graphId}/documents/${row.id}`)
}

const clearSelectedEntityType = () => {
  selectedEntityType.value = null
}

const showDeleteDialog = ref(false)
const deleteInProgress = ref(false)
const deletingDocument = ref<Document | null>(null)

const showDeleteEntityRecordDialog = ref(false)
const deleteEntityRecordInProgress = ref(false)
const deletingEntityRecord = ref<EntityRecord | null>(null)
const deletingEntityRecordIds = ref<Set<string>>(new Set())

const showDeleteEntityTypeDialog = ref(false)
const deleteEntityTypeInProgress = ref(false)
const deletingEntityType = ref<EntityTypeSummary | null>(null)
const deletingEntityTypes = ref<Set<string>>(new Set())

const confirmDelete = (row: Document) => {
  deletingDocument.value = row
  showDeleteDialog.value = true
}

const performDelete = async () => {
  if (!deletingDocument.value) return
  const row = deletingDocument.value
  try {
    deleteInProgress.value = true
    deletingIds.value.add(row.id)
    const endpoint = appStore.config.api.aiBridge.urlAdmin
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/documents/${row.id}`,
      method: 'DELETE',
      credentials: 'include',
    })
    if (response.ok) {
      documents.value = documents.value.filter((d) => d.id !== row.id)
      showDeleteDialog.value = false
    }
  } catch (e) {

  } finally {
    deleteInProgress.value = false
    deletingIds.value.delete(row.id)
  }
}

const openExternalLink = (url?: string) => {
  const target = (url || '').trim()
  if (!target) return
  window.open(target, '_blank', 'noopener')
}

const confirmDeleteEntityRecord = (row: EntityRecord) => {
  deletingEntityRecord.value = row
  showDeleteEntityRecordDialog.value = true
}

const confirmDeleteEntityType = (row: EntityTypeSummary) => {
  deletingEntityType.value = row
  showDeleteEntityTypeDialog.value = true
}

const performDeleteEntityType = async () => {
  if (!deletingEntityType.value) return
  const row = deletingEntityType.value
  try {
    deleteEntityTypeInProgress.value = true
    deletingEntityTypes.value.add(row.entity)
    const endpoint = appStore.config.api.aiBridge.urlAdmin
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/entities/records?entity=${encodeURIComponent(row.entity)}`,
      method: 'DELETE',
      credentials: 'include',
    })
    if (response.ok) {
      entityTypes.value = entityTypes.value.filter((t) => t.entity !== row.entity)
      showDeleteEntityTypeDialog.value = false
    }
  } catch (e) {

  } finally {
    deleteEntityTypeInProgress.value = false
    deletingEntityTypes.value.delete(row.entity)
  }
}

const performDeleteEntityRecord = async () => {
  if (!deletingEntityRecord.value) return
  const row = deletingEntityRecord.value
  try {
    deleteEntityRecordInProgress.value = true
    deletingEntityRecordIds.value.add(row.id)
    const endpoint = appStore.config.api.aiBridge.urlAdmin
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/entities/records/${row.id}`,
      method: 'DELETE',
      credentials: 'include',
    })
    if (response.ok) {
      entityRecords.value = entityRecords.value.filter((r) => r.id !== row.id)
      entityRecordsPagination.value.rowsNumber = Math.max(0, entityRecordsPagination.value.rowsNumber - 1)
      showDeleteEntityRecordDialog.value = false
    }
  } catch (e) {

  } finally {
    deleteEntityRecordInProgress.value = false
    deletingEntityRecordIds.value.delete(row.id)
  }
}

// Watch for view mode changes — always refresh when switching
watch(viewMode, (newMode) => {
  selectedEntityType.value = null
  if (newMode === 'documents') {
    fetchDocuments()
  } else if (newMode === 'entities') {
    fetchEntityTypes()
  }
})

onMounted(() => {
  viewMode.value = 'documents'
  fetchDocuments()
})

const refresh = () => {
  if (viewMode.value === 'documents') {
    fetchDocuments()
  } else if (viewMode.value === 'entities') {
    if (selectedEntityType.value) {
      fetchEntityRecords(selectedEntityType.value, entityRecordsPagination.value.page, entityRecordsPagination.value.rowsPerPage)
    } else {
      fetchEntityTypes()
    }
  }
}

// Expose refresh method so parent can trigger reloads after uploads
defineExpose({ refresh })
</script>

<style scoped>
.search-input {
  width: 250px;
}

.view-mode-toggle__track {
  position: relative;
  display: inline-flex;
  align-items: center;
  background: var(--q-light);
  border-radius: var(--radius-xl);
  padding: 4px;
  gap: 2px;
}

.view-mode-toggle__indicator {
  position: absolute;
  top: 4px;
  left: 4px;
  width: calc(50% - 5px);
  height: calc(100% - 8px);
  background: var(--q-white);
  border-radius: var(--radius-lg);
  box-shadow:
    0 1px 3px rgba(0, 0, 0, 0.1),
    0 1px 2px rgba(0, 0, 0, 0.06);
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 0;
}

.view-mode-toggle__indicator--right {
  transform: translateX(calc(100% + 2px));
}

.view-mode-toggle__btn {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 18px 1fr 18px;
  align-items: center;
  column-gap: 8px;
  flex: 0 0 132px;
  width: 100px;
  padding: 7px 16px;
  border: none;
  background: transparent;
  font-size: var(--km-font-size-body);
  font-weight: 500;
  color: var(--q-icon);
  cursor: pointer;
  border-radius: var(--radius-lg);
  transition: color 0.2s ease;
  white-space: nowrap;
  line-height: 1;
  font-family: inherit;
}

.view-mode-toggle__icon,
.view-mode-toggle__icon-spacer {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
}

.view-mode-toggle__label {
  text-align: center;
}

.view-mode-toggle__btn:hover:not(.view-mode-toggle__btn--active) {
  color: var(--q-secondary-text);
}

.view-mode-toggle__btn--active {
  color: var(--q-primary);
}
</style>
