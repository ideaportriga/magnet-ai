<template>
  <div>
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
      v-model:pagination="pagination"
      flat
      table-header-class="bg-primary-light"
      :rows="filteredDocuments"
      :columns="documentsColumns"
      row-key="id"
      :rows-per-page-options="[10]"
      @row-click="handleDocumentClick"
    >
      <template #body-cell-menu="slotScope">
        <q-td :props="slotScope" class="sticky-col">
          <div class="flex items-center justify-end no-wrap q-gutter-x-xs">
            <km-btn
              flat
              color="secondary-text"
              label-class="km-button-text"
              icon-size="16px"
              icon="fa fa-external-link"
              :disable="!slotScope.row.external_link"
              @click.stop="emit('open-external-link', slotScope.row.external_link)"
            />
            <q-btn dense flat color="dark" icon="more_vert" :disable="deletingIds.has(slotScope.row.id)" @click.stop>
              <q-menu anchor="bottom right" self="top right" auto-close>
                <q-list dense>
                  <q-item clickable @click="emit('delete-document', slotScope.row)">
                    <q-item-section thumbnail>
                      <q-icon name="delete" color="negative" size="20px" class="q-ml-sm" />
                    </q-item-section>
                    <q-item-section>Delete</q-item-section>
                  </q-item>
                </q-list>
              </q-menu>
            </q-btn>
          </div>
        </q-td>
      </template>
      <template #body-cell-name="slotScope">
        <q-td :props="slotScope">
          <div class="row items-center no-wrap q-gutter-x-sm">
            <kg-file-type-badge :type="slotScope.row.type" />
            <div class="text-body2 text-weight-medium ellipsis" style="max-width: 300px">
              {{ slotScope.row.title }}
              <q-tooltip>{{ slotScope.row.title }}</q-tooltip>
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
</template>

<script setup lang="ts">
import { formatDuration, formatRelative } from '@shared/utils'
import type { QTableColumn } from 'quasar'
import { computed, ref } from 'vue'
import { KgFileTypeBadge, KgStatusBadge } from '../common'
import type { Document } from './models'

const props = defineProps<{
  documents: Document[]
  searchQuery: string
  deletingIds: Set<string>
}>()

const emit = defineEmits<{
  'document-click': [row: Document]
  'delete-document': [row: Document]
  'open-external-link': [url?: string]
}>()

const pagination = ref({ rowsPerPage: 10, page: 1 })

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
    style: 'width: 80px',
    headerStyle: 'width: 80px',
  },
]

const filteredDocuments = computed(() => {
  if (!props.searchQuery) {
    return props.documents
  }

  const search = props.searchQuery.toLowerCase()
  return props.documents.filter(
    (doc) =>
      doc.name?.toLowerCase().includes(search) ||
      doc.description?.toLowerCase().includes(search) ||
      doc.source_name?.toLowerCase().includes(search)
  )
})

const handleDocumentClick = (_event: Event, row: Document) => {
  emit('document-click', row)
}
</script>

<style scoped>
:deep(.q-table thead th) {
  font-size: 14px;
  font-weight: 600;
}

:deep(.q-table tbody td) {
  height: 40px;
  padding: 2px 16px;
}

:deep(.sticky-col) {
  position: sticky;
  right: 0;
  z-index: 1;
  background: white;
}

:deep(tr:hover .sticky-col) {
  background: white;
}

:deep(thead th:last-child) {
  position: sticky;
  right: 0;
  z-index: 2;
  background: inherit;
}
</style>
