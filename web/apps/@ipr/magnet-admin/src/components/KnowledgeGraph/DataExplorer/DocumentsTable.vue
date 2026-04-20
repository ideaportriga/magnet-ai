<template>
  <div class="km-table-scroll">
    <!--
      §E.2.3 — migrated from q-table to km-data-table (TanStack Table).
      Documents are received via prop and paginated client-side, so
      useLocalDataTable is a perfect fit. Custom cells replace the
      former q-table body-cell-NAME slots.
    -->
    <km-data-table
      :table="table"
      row-key="id"
      @row-click="handleDocumentClick"
    >
      <template #cell-name="{ row }">
        <div class="row items-center no-wrap q-gutter-x-sm">
          <kg-file-type-badge :type="row.type" />
          <div class="text-body2 text-weight-medium ellipsis" style="max-width: 300px">
            {{ row.title }}
            <q-tooltip>{{ row.title }}</q-tooltip>
          </div>
        </div>
      </template>

      <template #cell-chunks_count="{ row }">
        {{ row.chunks_count || 0 }}
      </template>

      <template #cell-processing_time="{ row }">
        {{ formatDuration(row.processing_time && row.processing_time * 1000) }}
      </template>

      <template #cell-updated_at="{ row }">
        {{ formatRelative(row.updated_at) }}
      </template>

      <template #cell-created_at="{ row }">
        {{ formatRelative(row.created_at) }}
      </template>

      <template #cell-status="{ row }">
        <kg-status-badge :status="row.status" :message="row.status_message" />
      </template>

      <template #cell-menu="{ row }">
        <div class="flex items-center justify-end no-wrap q-gutter-x-xs">
          <km-btn
            flat
            color="secondary-text"
            label-class="km-button-text"
            icon-size="16px"
            icon="fa fa-external-link"
            :disable="!row.external_link"
            @click.stop="emit('open-external-link', row.external_link)"
          />
          <q-btn dense flat color="dark" icon="more_vert" :disable="deletingIds.has(row.id)" @click.stop>
            <q-menu anchor="bottom right" self="top right" auto-close>
              <q-list dense>
                <q-item clickable @click="emit('delete-document', row)">
                  <q-item-section thumbnail>
                    <q-icon name="delete" color="negative" size="20px" class="q-ml-sm" />
                  </q-item-section>
                  <q-item-section>{{ m.common_delete() }}</q-item-section>
                </q-item>
              </q-list>
            </q-menu>
          </q-btn>
        </div>
      </template>
    </km-data-table>
  </div>
</template>

<script setup lang="ts">
import { formatDuration, formatRelative } from '@shared/utils'
import { m } from '@/paraglide/messages'
import type { ColumnDef } from '@tanstack/vue-table'
import { toRef } from 'vue'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { KgFileTypeBadge, KgStatusBadge } from '../common'
import type { Document } from './models'

const props = defineProps<{
  documents: Document[]
  deletingIds: Set<string>
}>()

const emit = defineEmits<{
  'document-click': [row: Document]
  'delete-document': [row: Document]
  'open-external-link': [url?: string]
}>()

// §E.2.3 — TanStack columns. Complex rendering (badges, formatters,
// tooltips) happens in named cell slots above; the column meta only
// captures alignment + header label + sort behaviour.
const documentsColumns: ColumnDef<Document, unknown>[] = [
  {
    id: 'name',
    accessorKey: 'title',
    header: m.common_document(),
    enableSorting: true,
    meta: { align: 'left' },
  },
  {
    id: 'source_name',
    accessorKey: 'source_name',
    header: m.common_source(),
    enableSorting: true,
    meta: { align: 'left' },
  },
  {
    id: 'content_profile',
    accessorKey: 'content_profile',
    header: m.common_profile(),
    enableSorting: true,
    meta: { align: 'left' },
  },
  {
    id: 'chunks_count',
    accessorKey: 'chunks_count',
    header: m.common_chunks(),
    enableSorting: true,
    meta: { align: 'right' },
  },
  {
    id: 'status',
    accessorKey: 'status',
    header: m.common_status(),
    enableSorting: true,
    meta: { align: 'left' },
  },
  {
    id: 'processing_time',
    accessorKey: 'processing_time',
    header: m.common_processingTime(),
    enableSorting: true,
    meta: { align: 'right' },
  },
  {
    id: 'updated_at',
    accessorKey: 'updated_at',
    header: m.common_updated(),
    enableSorting: true,
    meta: { align: 'left' },
  },
  {
    id: 'created_at',
    accessorKey: 'created_at',
    header: m.common_created(),
    enableSorting: true,
    meta: { align: 'left' },
  },
  {
    id: 'menu',
    header: '',
    enableSorting: false,
    meta: { align: 'right', width: '80px' },
  },
]

const { table } = useLocalDataTable<Document>(
  toRef(props, 'documents'),
  documentsColumns,
  { defaultPageSize: 10 },
)

function handleDocumentClick(row: Document) {
  emit('document-click', row)
}
</script>

<style scoped>
:deep(.sticky-col) {
  position: sticky;
  right: 0;
  z-index: 1;
  background: var(--q-white);
}
:deep(tr:hover .sticky-col) {
  background: var(--q-white);
}
:deep(thead th:last-child) {
  position: sticky;
  right: 0;
  z-index: 2;
  background: inherit;
}
</style>
