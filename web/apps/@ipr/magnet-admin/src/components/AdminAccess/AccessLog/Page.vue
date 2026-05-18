<template>
  <km-list-page>
    <template #toolbar>
      <div class="cluster" data-gap="sm" data-wrap="yes" data-align="end" style="flex: 1">
        <div class="stack" data-gap="xs" style="min-inline-size: 180px">
          <label class="km-description">Action</label>
          <km-input
            v-model="actionFilter"
            placeholder="e.g. role.update"
            clearable
            @keydown.enter="apply"
          />
        </div>
        <div class="stack" data-gap="xs" style="min-inline-size: 160px">
          <label class="km-description">Target type</label>
          <km-input
            v-model="targetTypeFilter"
            placeholder="e.g. role, user"
            clearable
            @keydown.enter="apply"
          />
        </div>
        <div class="stack" data-gap="xs" style="min-inline-size: 220px">
          <label class="km-description">Actor ID</label>
          <km-input
            v-model="actorIdFilter"
            placeholder="UUID"
            clearable
            @keydown.enter="apply"
          />
        </div>
        <km-btn label="Apply" @click="apply" />
        <km-btn flat label="Clear" @click="clearFilters" />
      </div>
    </template>

    <div class="stack" data-gap="sm" style="block-size: 100%; min-block-size: 0">
      <km-data-table
        :table="table"
        :loading="isLoading"
        :fetching="isFetching"
        fill-height
        row-key="id"
        no-records-label="No log entries match the current filters."
        hide-pagination
        style="flex: 1; min-block-size: 0"
      />
      <div class="cluster" data-justify="between" data-align="center" data-wrap="no">
        <span class="km-description text-grey">
          Showing {{ entries.length }} entr{{ entries.length === 1 ? 'y' : 'ies' }}
          starting at offset {{ offset }}
        </span>
        <div class="cluster" data-gap="sm" data-wrap="no">
          <km-btn
            icon="chevron-left"
            flat
            label="Prev"
            :disabled="offset === 0 || isFetching"
            @click="prevPage"
          />
          <km-btn
            icon="chevron-right"
            flat
            label="Next"
            :disabled="entries.length < limit || isFetching"
            @click="nextPage"
          />
        </div>
      </div>
    </div>
  </km-list-page>
</template>

<script setup lang="ts">
import { computed, h, ref } from 'vue'
import { useQuery, keepPreviousData } from '@tanstack/vue-query'
import type { ColumnDef, Row } from '@tanstack/vue-table'
import { formatDateTime } from '@shared/utils'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { listAccessLog, type AccessAuditEntry } from '@/api/adminAccess'
import KmChip from '@ds/components/domain/KmChip.vue'

const actionFilter = ref('')
const targetTypeFilter = ref('')
const actorIdFilter = ref('')
const limit = 50
const offset = ref(0)

/**
 * Applied filters are a snapshot — input edits don't refire the query.
 * Apply / Enter / Clear / page nav all bump this snapshot, which keys the
 * useQuery cache.
 */
const applied = ref({
  action: '',
  target_type: '',
  actor_id: '',
})

const queryParams = computed(() => ({
  ...applied.value,
  limit,
  offset: offset.value,
}))

const accessLogQuery = useQuery({
  queryKey: computed(() => ['admin', 'access-log', queryParams.value] as const),
  queryFn: () =>
    listAccessLog({
      action: applied.value.action || undefined,
      target_type: applied.value.target_type || undefined,
      actor_id: applied.value.actor_id || undefined,
      limit,
      offset: offset.value,
    }),
  placeholderData: keepPreviousData,
})
const entries = computed<AccessAuditEntry[]>(() => accessLogQuery.data.value ?? [])
const isLoading = computed(() => accessLogQuery.isLoading.value)
const isFetching = computed(() => accessLogQuery.isFetching.value)

// ── Expandable payload state ─────────────────────────────────────────
const expanded = ref<Set<string>>(new Set())
function toggleExpand(id: string) {
  const next = new Set(expanded.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  expanded.value = next
}

function formatPayload(payload: Record<string, unknown>): string {
  try {
    return JSON.stringify(payload, null, 2)
  } catch {
    return String(payload)
  }
}

const columns: ColumnDef<AccessAuditEntry, unknown>[] = [
  {
    id: 'created_at',
    accessorKey: 'created_at',
    header: 'Timestamp',
    cell: ({ row }) => formatDateTime(row.original.created_at),
    enableSorting: true,
    meta: { width: '180px' },
  },
  {
    id: 'action',
    accessorKey: 'action',
    header: 'Action',
    cell: ({ row }) =>
      h(KmChip, { tone: 'brand', size: 'sm', label: row.original.action }),
    enableSorting: true,
    meta: { width: '220px' },
  },
  {
    id: 'target_type',
    accessorKey: 'target_type',
    header: 'Target',
    cell: ({ row }) => {
      const e = row.original
      return h('div', { class: 'stack', 'data-gap': 'xs' }, [
        h(KmChip, { tone: 'muted', size: 'sm', label: e.target_type }),
        e.target_id
          ? h(
              'span',
              { class: 'km-description text-grey font-mono', style: 'word-break: break-all' },
              e.target_id,
            )
          : null,
      ])
    },
    enableSorting: true,
  },
  {
    id: 'actor_id',
    accessorKey: 'actor_id',
    header: 'Actor',
    cell: ({ row }) =>
      row.original.actor_id
        ? h(
            'span',
            { class: 'font-mono km-description', style: 'word-break: break-all' },
            row.original.actor_id,
          )
        : h('span', { class: 'km-description text-grey' }, 'system'),
    enableSorting: false,
    meta: { width: '280px' },
  },
  {
    id: 'payload',
    accessorFn: (e) => Object.keys(e.payload ?? {}).length,
    header: 'Payload',
    cell: ({ row }: { row: Row<AccessAuditEntry> }) => {
      const e = row.original
      const hasPayload = e.payload && Object.keys(e.payload).length > 0
      if (!hasPayload) {
        return h('span', { class: 'km-description text-grey' }, '—')
      }
      const isOpen = expanded.value.has(e.id)
      const toggleBtn = h(
        'button',
        {
          type: 'button',
          class: 'km-link',
          onClick: (ev: Event) => {
            ev.stopPropagation()
            toggleExpand(e.id)
          },
        },
        isOpen ? 'Hide' : `${Object.keys(e.payload).length} field(s)`,
      )
      return h('div', { class: 'stack', 'data-gap': 'xs' }, [
        toggleBtn,
        isOpen
          ? h(
              'pre',
              {
                class: 'font-mono bg-grey-bg p-sm border-radius-6',
                style:
                  'white-space: pre-wrap; word-break: break-word; max-block-size: 200px; overflow: auto; margin: 0',
              },
              formatPayload(e.payload),
            )
          : null,
      ])
    },
    enableSorting: false,
    meta: { class: 'km-data-table__td--wrap' },
  },
]

const { table } = useLocalDataTable<AccessAuditEntry>(entries, columns, {
  defaultSort: [{ id: 'created_at', desc: true }],
  defaultPageSize: limit,
})

function apply() {
  offset.value = 0
  applied.value = {
    action: actionFilter.value.trim(),
    target_type: targetTypeFilter.value.trim(),
    actor_id: actorIdFilter.value.trim(),
  }
}

function clearFilters() {
  actionFilter.value = ''
  targetTypeFilter.value = ''
  actorIdFilter.value = ''
  apply()
}

function nextPage() {
  offset.value += limit
}

function prevPage() {
  offset.value = Math.max(0, offset.value - limit)
}
</script>

<style scoped>
.km-link {
  background: transparent;
  border: none;
  padding: 0;
  color: var(--km-color-text-brand, #2962ff);
  cursor: pointer;
  font-size: 0.875rem;
}
.km-link:hover {
  text-decoration: underline;
}
</style>
