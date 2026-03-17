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

      <div class="row items-center q-mb-md q-gutter-sm">
        <q-btn v-if="viewMode === 'entities' && selectedEntityType" flat dense icon="arrow_back" @click="clearSelectedEntityType" />
        <div v-if="viewMode === 'entities' && selectedEntityType" class="km-heading-8">{{ selectedEntityType }}</div>
        <km-input v-if="hasRecords" v-model="searchQuery" placeholder="Search..." icon-before="search" clearable style="width: 250px" />
        <q-space />
        <km-btn flat icon="refresh" label="Refresh" @click="refresh" />
      </div>

      <q-linear-progress v-if="loading" indeterminate color="primary" />

      <documents-table
        v-if="viewMode === 'documents' && !loading"
        :documents="documents"
        :search-query="searchQuery"
        :deleting-ids="deletingIds"
        @document-click="onDocumentClick"
        @delete-document="confirmDelete"
        @open-external-link="openExternalLink"
      />

      <entities-table
        v-if="viewMode === 'entities' && !loading"
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
import { useStore } from 'vuex'
import { KgConfirmDialog } from '../common'
import DocumentsTable from './DocumentsTable.vue'
import EntitiesTable from './EntitiesTable.vue'
import type { Document, EntityRecord, EntityTypeSummary } from './models'

const props = defineProps<{
  graphId: string
  graphDetails: Record<string, unknown>
}>()

const router = useRouter()
const store = useStore()

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

const fetchEntityTypes = async () => {
  loading.value = true
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
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
    console.error('Error fetching entity types:', error)
    entityTypes.value = []
  } finally {
    loading.value = false
  }
}

const fetchEntityRecords = async (entity: string, page = 1, rowsPerPage = 10) => {
  loading.value = true
  try {
    const offset = (page - 1) * rowsPerPage
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
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
    console.error('Error fetching entity records:', error)
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
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
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
    console.error('Failed to delete document', e)
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
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
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
    console.error('Failed to delete entity type records', e)
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
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
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
    console.error('Failed to delete entity record', e)
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
.view-mode-toggle__track {
  position: relative;
  display: inline-flex;
  align-items: center;
  background: #f0f1f4;
  border-radius: 10px;
  padding: 4px;
  gap: 2px;
}

.view-mode-toggle__indicator {
  position: absolute;
  top: 4px;
  left: 4px;
  width: calc(50% - 5px);
  height: calc(100% - 8px);
  background: #ffffff;
  border-radius: 8px;
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
  font-size: 14px;
  font-weight: 500;
  color: #8b8fa3;
  cursor: pointer;
  border-radius: 8px;
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
  color: #5f6377;
}

.view-mode-toggle__btn--active {
  color: var(--q-primary);
}
</style>
