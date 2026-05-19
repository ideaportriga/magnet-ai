<template>
  <div>
    <q-table
      v-model:pagination="pagination"
      flat
      table-header-class="bg-primary-light"
      :rows="documents"
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
            <q-btn
              dense
              flat
              color="dark"
              icon="more_vert"
              :disable="deletingIds.has(slotScope.row.id) || extractingMetadataIds.has(slotScope.row.id) || extractingEntityIds.has(slotScope.row.id)"
              @click.stop
            >
              <q-menu anchor="bottom right" self="top right" auto-close>
                <q-list dense>
                  <q-item clickable @click="emit('extract-metadata', slotScope.row)">
                    <q-item-section thumbnail>
                      <q-icon name="fact_check" color="primary" size="20px" class="q-ml-sm" />
                    </q-item-section>
                    <q-item-section>Run metadata extraction</q-item-section>
                  </q-item>
                  <q-item clickable @click="emit('extract-entities', slotScope.row)">
                    <q-item-section thumbnail>
                      <q-icon name="account_tree" color="primary" size="20px" class="q-ml-sm" />
                    </q-item-section>
                    <q-item-section>Run entity extraction</q-item-section>
                  </q-item>
                  <q-separator />
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
          <div class="kg-doc-status">
            <kg-pipeline-strip :phases="phasesForDoc(slotScope.row)" mode="compact" />
            <div v-if="slotScope.row.status_message" class="kg-doc-status__message">
              {{ slotScope.row.status_message }}
            </div>
          </div>
        </q-td>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
import { formatDuration, formatRelative } from '@shared/utils'
import type { QTableColumn } from 'quasar'
import { ref } from 'vue'
import { KgFileTypeBadge, KgPipelineStrip, type KgPhaseState, type KgPipelinePhase } from '../common'
import type { Document, DocumentPipelinePhase, DocumentPipelineState } from './models'

const props = defineProps<{
  documents: Document[]
  deletingIds: Set<string>
  extractingMetadataIds: Set<string>
  extractingEntityIds: Set<string>
}>()

const emit = defineEmits<{
  'document-click': [row: Document]
  'delete-document': [row: Document]
  'open-external-link': [url?: string]
  'extract-metadata': [row: Document]
  'extract-entities': [row: Document]
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

const handleDocumentClick = (_event: Event, row: Document) => {
  emit('document-click', row)
}

// --- Pipeline strip --------------------------------------------------------
//
// Each document carries a `pipeline_state` block from the backend that
// describes its position in the Sync -> Metadata -> Entities pipeline. We map
// the raw payload into the shape the shared strip component renders.

const ALLOWED_STATES = new Set<KgPhaseState>(['pending', 'running', 'completed', 'failed', 'skipped', 'not_run'])

function normalizeState(raw: string | undefined | null): KgPhaseState {
  const v = String(raw || '').toLowerCase()
  if (v === 'error') return 'failed'
  if (v === 'processing') return 'running'
  if (ALLOWED_STATES.has(v as KgPhaseState)) return v as KgPhaseState
  return 'not_run'
}

function tooltipLinesFor(phase: DocumentPipelinePhase | undefined): string[] {
  if (!phase) return []
  const lines: string[] = []
  if (phase.completed_at) lines.push(`Completed: ${new Date(phase.completed_at).toLocaleString()}`)
  if (phase.failed_at) lines.push(`Failed: ${new Date(phase.failed_at).toLocaleString()}`)
  if (phase.fields_count != null) lines.push(`${phase.fields_count} fields`)
  if (phase.error_message) lines.push(phase.error_message)
  return lines
}

function phasesForDoc(row: Document): KgPipelinePhase[] {
  const ps: DocumentPipelineState | null | undefined = row.pipeline_state
  const sync = ps?.sync
  const meta = ps?.metadata_extraction
  const ent = ps?.entity_extraction
  return [
    {
      phase: 'sync',
      state: sync ? normalizeState(sync.status) : normalizeState(row.status),
      tooltipLines: tooltipLinesFor(sync),
    },
    { phase: 'metadata', state: normalizeState(meta?.status), tooltipLines: tooltipLinesFor(meta) },
    { phase: 'entities', state: normalizeState(ent?.status), tooltipLines: tooltipLinesFor(ent) },
  ]
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

.kg-doc-status {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 5px;
  min-width: 220px;
}

.kg-doc-status__message {
  max-width: 260px;
  color: var(--q-secondary-text, rgba(0, 0, 0, 0.55));
  font-size: 11px;
  line-height: 1.25;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
