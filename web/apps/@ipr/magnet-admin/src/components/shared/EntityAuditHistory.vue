<template>
  <div class="stack full-height" data-gap="md">
    <div class="cluster" data-justify="between" data-align="center" data-wrap="no">
      <div class="km-description text-grey">
        <span v-if="isLoading">Loading…</span>
        <span v-else>
          {{ entries.length }} entr{{ entries.length === 1 ? 'y' : 'ies' }}
        </span>
      </div>
      <km-btn
        flat
        icon="refresh"
        icon-size="14px"
        label="Refresh"
        :loading="isFetching"
        @click="refetch"
      />
    </div>

    <km-data-table
      :table="table"
      :loading="isLoading"
      :fetching="isFetching"
      fill-height
      row-key="id"
      no-records-label="No changes have been recorded for this entity."
      hide-pagination
      class="entity-audit__table"
      style="min-block-size: 0; flex: 1"
      @row-click="(row) => openDetail((row as EntityAuditEntry).id)"
    />

    <DsDialog v-model:open="detailOpen" size="xl">
      <template #title>
        <span class="text-capitalize">{{ detailEntry?.action ?? '—' }}</span>
        <span class="text-grey"> · {{ detailEntry ? formatDateTime(detailEntry.created_at) : '' }}</span>
      </template>
      <template #description>
        {{ detailEntry?.actor_display || detailEntry?.actor_type || '' }}
        <span v-if="detailEntry?.source"> · {{ detailEntry.source }}</span>
      </template>

      <div v-if="detailLoading" class="stack p-lg" data-gap="md" data-align="center">
        <km-inner-loading :showing="true" />
      </div>

      <div v-else class="stack overflow-auto" data-gap="lg" style="min-block-size: 0; max-block-size: 70vh">
        <section class="stack" data-gap="xs">
          <div class="cluster" data-justify="between" data-align="center" data-wrap="no">
            <div class="km-heading-7">
              {{ diffEntries.length }} changed field{{ diffEntries.length === 1 ? '' : 's' }}
            </div>
            <km-input
              v-if="diffEntries.length > 4"
              v-model="diffFilter"
              placeholder="Filter by path"
              clearable
              dense
              style="max-inline-size: 240px"
            />
          </div>

          <div v-if="filteredDiffEntries.length === 0" class="km-description text-grey p-md">
            <span v-if="diffEntries.length === 0">No field-level changes were captured for this entry.</span>
            <span v-else>No paths match the filter.</span>
          </div>

          <div v-else class="entity-audit__diff-table">
            <div
              v-for="[path, change] in filteredDiffEntries"
              :key="path"
              class="entity-audit__diff-row"
            >
              <div class="cluster" data-align="center" data-wrap="no" data-gap="xs">
                <span class="entity-audit__diff-path font-mono">{{ path }}</span>
                <km-chip
                  v-if="changeKind(change) !== 'change'"
                  size="sm"
                  :tone="changeKind(change) === 'add' ? 'success' : 'destructive'"
                  :label="changeKind(change) === 'add' ? 'added' : 'removed'"
                />
              </div>

              <!-- Inline format for short scalar changes — much easier to scan. -->
              <div
                v-if="isInlineDisplayable(change)"
                class="cluster entity-audit__diff-inline"
                data-gap="sm"
                data-align="center"
                data-wrap="yes"
              >
                <span class="entity-audit__chip entity-audit__chip--from font-mono">
                  <span class="entity-audit__sign">−</span>
                  <span class="entity-audit__chip-text">{{ formatScalar(change.from) }}</span>
                </span>
                <km-glyph name="arrow-right" size="14px" tone="muted" />
                <span class="entity-audit__chip entity-audit__chip--to font-mono">
                  <span class="entity-audit__sign">+</span>
                  <span class="entity-audit__chip-text">{{ formatScalar(change.to) }}</span>
                </span>
              </div>

              <!-- Git-style unified line diff for complex / multi-line values. -->
              <div v-else class="entity-audit__unified-diff">
                <div
                  v-for="(line, idx) in unifiedDiffFor(change)"
                  :key="idx"
                  class="entity-audit__diff-line"
                  :class="diffLineClass(line)"
                >
                  <template v-if="line.kind === 'separator'">
                    <span class="entity-audit__diff-marker">…</span>
                    <span class="entity-audit__diff-lineno" />
                    <span class="entity-audit__diff-lineno" />
                    <span class="entity-audit__diff-text entity-audit__diff-text--meta">
                      {{ line.collapsed }} unchanged line{{ line.collapsed === 1 ? '' : 's' }}
                    </span>
                  </template>
                  <template v-else>
                    <span class="entity-audit__diff-marker">{{ diffLineMarker(line.kind) }}</span>
                    <span class="entity-audit__diff-lineno">{{ line.before ?? '' }}</span>
                    <span class="entity-audit__diff-lineno">{{ line.after ?? '' }}</span>
                    <span class="entity-audit__diff-text">{{ line.text || ' ' }}</span>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section v-if="hasFullSnapshots" class="stack" data-gap="xs">
          <button type="button" class="entity-audit__toggle" @click="showFullSnapshots = !showFullSnapshots">
            <km-glyph :name="showFullSnapshots ? 'chevron-down' : 'chevron-right'" size="12px" />
            <span>{{ showFullSnapshots ? 'Hide' : 'Show' }} full state</span>
          </button>

          <div v-if="showFullSnapshots" class="entity-audit__snapshots">
            <div v-if="detailDetail?.snapshot_before" class="stack" data-gap="2xs">
              <div class="km-description text-grey">Snapshot before</div>
              <pre class="entity-audit__snapshot font-mono">{{ formatValue(detailDetail.snapshot_before) }}</pre>
            </div>
            <div v-if="detailDetail?.snapshot_after" class="stack" data-gap="2xs">
              <div class="km-description text-grey">Snapshot after</div>
              <pre class="entity-audit__snapshot font-mono">{{ formatValue(detailDetail.snapshot_after) }}</pre>
            </div>
          </div>
        </section>
      </div>

      <template #footer>
        <km-btn flat label="Close" @click="detailOpen = false" />
        <km-btn
          v-if="canRestore"
          icon="undo"
          :label="restoreLabel"
          :loading="restoring"
          :disable="restoring"
          @click="confirmRestore"
        />
      </template>
    </DsDialog>

    <km-popup-confirm
      :visible="confirmingRestore"
      confirm-button-label="Restore"
      cancel-button-label="Cancel"
      notification-icon="warning"
      @confirm="doRestore"
      @cancel="confirmingRestore = false"
    >
      <div class="cluster km-heading-7" data-justify="center">
        Restore this version?
      </div>
      <div class="cluster text-center" data-justify="center">
        The entity's current state will be replaced with the snapshot from this audit entry.
        A new audit row will record the restore.
      </div>
    </km-popup-confirm>
  </div>
</template>

<script setup lang="ts">
import { computed, h, ref, watch } from 'vue'
import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/vue-query'
import type { ColumnDef } from '@tanstack/vue-table'
import { formatDateTime } from '@shared/utils'
import { notify } from '@shared/utils/notify'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import {
  listEntityAudit,
  getEntityAuditEntry,
  restoreEntityAuditEntry,
  type EntityAuditEntry,
  type EntityAuditDetail,
  type EntityAuditDiffValue,
} from '@/api/entityAudit'
import { DsDialog } from '@ds/primitives'
import KmChip from '@ds/components/domain/KmChip.vue'
import {
  unifiedLineDiff,
  collapseContext,
  toDiffText,
  type DiffEntry,
  type LineKind,
} from '@/utils/lineDiff'

const props = withDefaults(
  defineProps<{
    /** Audit slug, e.g. "agent", "prompt_template" */
    entityType: string
    /** UUID of the entity */
    entityId: string
    /** Allow the user to restore older versions */
    allowRestore?: boolean
    /** Query-key namespaces invalidated after a successful restore */
    invalidateQueryKeys?: readonly (readonly unknown[])[]
  }>(),
  {
    allowRestore: true,
    invalidateQueryKeys: () => [],
  },
)

const emit = defineEmits<{
  /** Fires after a successful restore. Hosts re-fetch their entity. */
  (e: 'restored', payload: { auditId: string; restoreAuditId: string | null }): void
}>()

const queryClient = useQueryClient()

const listQuery = useQuery({
  queryKey: computed(
    () =>
      [
        'entity-audit',
        'list',
        { entity_type: props.entityType, entity_id: props.entityId },
      ] as const,
  ),
  queryFn: () =>
    listEntityAudit({
      entity_type: props.entityType,
      entity_id: props.entityId,
      limit: 200,
    }),
  placeholderData: keepPreviousData,
})

const entries = computed<EntityAuditEntry[]>(() => listQuery.data.value ?? [])
const isLoading = computed(() => listQuery.isLoading.value)
const isFetching = computed(() => listQuery.isFetching.value)

function refetch() {
  void listQuery.refetch()
}

// ── Detail dialog ────────────────────────────────────────────────────
const detailOpen = ref(false)
const selectedId = ref<string | null>(null)

const detailQuery = useQuery({
  queryKey: computed(() => ['entity-audit', 'detail', selectedId.value] as const),
  queryFn: () => {
    if (!selectedId.value) return Promise.reject(new Error('No selected id'))
    return getEntityAuditEntry(selectedId.value)
  },
  enabled: computed(() => detailOpen.value && !!selectedId.value),
})

const detailEntry = computed<EntityAuditEntry | null>(() => {
  if (!selectedId.value) return null
  return entries.value.find((e) => e.id === selectedId.value) ?? null
})
const detailDetail = computed<EntityAuditDetail | null>(
  () => detailQuery.data.value ?? null,
)
const detailLoading = computed(() => detailQuery.isLoading.value)

const diffEntries = computed<[string, EntityAuditDiffValue][]>(() => {
  const diff = detailDetail.value?.diff ?? detailEntry.value?.diff ?? {}
  return Object.entries(diff).sort(([a], [b]) => a.localeCompare(b))
})

const diffFilter = ref('')
const filteredDiffEntries = computed<[string, EntityAuditDiffValue][]>(() => {
  const q = diffFilter.value.trim().toLowerCase()
  if (!q) return diffEntries.value
  return diffEntries.value.filter(([path]) => path.toLowerCase().includes(q))
})

const showFullSnapshots = ref(false)
const hasFullSnapshots = computed(
  () => !!(detailDetail.value?.snapshot_before || detailDetail.value?.snapshot_after),
)

/** Classify the change so we can label "added" / "removed" / scalar swap. */
function changeKind(change: EntityAuditDiffValue): 'add' | 'remove' | 'change' {
  if (change.from === null || change.from === undefined) return 'add'
  if (change.to === null || change.to === undefined) return 'remove'
  return 'change'
}

/** Compact inline rendering only when BOTH sides are short scalars — keeps the
 *  "x → y" presentation readable. Strings get JSON-quoted; everything else
 *  prints with `String()`. */
function isInlineDisplayable(change: EntityAuditDiffValue): boolean {
  return isScalar(change.from) && isScalar(change.to) && shortText(change.from) && shortText(change.to)
}

function isScalar(v: unknown): boolean {
  if (v === null || v === undefined) return true
  const t = typeof v
  return t === 'string' || t === 'number' || t === 'boolean'
}

function shortText(v: unknown): boolean {
  if (typeof v === 'string') return v.length <= 80
  return true
}

function formatScalar(v: unknown): string {
  if (v === null || v === undefined) return '∅'
  if (typeof v === 'string') return JSON.stringify(v)
  return String(v)
}

/** Build a git-style unified diff for a single audit field. Memoized per
 *  selection so reactivity (filter / scroll) doesn't recompute LCS each
 *  render. */
const unifiedDiffCache = computed<Map<string, DiffEntry[]>>(() => {
  const m = new Map<string, DiffEntry[]>()
  for (const [path, change] of filteredDiffEntries.value) {
    if (isInlineDisplayable(change)) continue
    const lines = unifiedLineDiff(toDiffText(change.from), toDiffText(change.to))
    m.set(path, collapseContext(lines, 3))
  }
  return m
})

function unifiedDiffFor(change: EntityAuditDiffValue): DiffEntry[] {
  // The cache is keyed by path; the calling template iterates the path/change
  // pair via `filteredDiffEntries`, so we look up by reference instead. The
  // path is found by linear search over a typically-small set.
  for (const [path, c] of filteredDiffEntries.value) {
    if (c === change) return unifiedDiffCache.value.get(path) ?? []
  }
  return []
}

function diffLineMarker(kind: LineKind): string {
  if (kind === 'add') return '+'
  if (kind === 'del') return '−'
  return ' '
}

function diffLineClass(line: DiffEntry): string {
  if (line.kind === 'separator') return 'entity-audit__diff-line--sep'
  if (line.kind === 'add') return 'entity-audit__diff-line--add'
  if (line.kind === 'del') return 'entity-audit__diff-line--del'
  return 'entity-audit__diff-line--ctx'
}

function openDetail(id: string) {
  selectedId.value = id
  detailOpen.value = true
  // Reset transient UI state every time a new entry is opened.
  diffFilter.value = ''
  showFullSnapshots.value = false
}

watch(detailOpen, (open) => {
  if (!open) selectedId.value = null
})

// ── Restore ──────────────────────────────────────────────────────────
const canRestore = computed(() => {
  if (!props.allowRestore) return false
  const action = detailEntry.value?.action
  // 'create' rows have no earlier state to restore to.
  return action !== 'create'
})

const restoreLabel = computed(() => {
  const action = detailEntry.value?.action
  if (action === 'delete') return 'Restore deleted entity'
  return 'Restore this version'
})

const confirmingRestore = ref(false)
function confirmRestore() {
  confirmingRestore.value = true
}

const restoreMutation = useMutation({
  mutationFn: (auditId: string) => restoreEntityAuditEntry(auditId),
})
const restoring = computed(() => restoreMutation.isPending.value)

async function doRestore() {
  confirmingRestore.value = false
  const id = selectedId.value
  if (!id) return
  try {
    const result = await restoreMutation.mutateAsync(id)
    notify.success('Entity restored from this version.')
    await queryClient.invalidateQueries({
      queryKey: ['entity-audit', 'list', { entity_type: props.entityType, entity_id: props.entityId }],
    })
    for (const key of props.invalidateQueryKeys ?? []) {
      await queryClient.invalidateQueries({ queryKey: key as readonly unknown[] })
    }
    emit('restored', { auditId: id, restoreAuditId: result.restore_audit_id ?? null })
    detailOpen.value = false
  } catch (err: unknown) {
    notify.error(
      err instanceof Error ? err.message : 'Could not restore from this version',
    )
  }
}

// ── Table ────────────────────────────────────────────────────────────
function actionTone(action: string) {
  switch (action) {
    case 'create':
      return 'success'
    case 'update':
      return 'brand'
    case 'delete':
      return 'destructive'
    case 'restore':
      return 'warning'
    default:
      return 'muted'
  }
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return '—'
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

function diffCount(e: EntityAuditEntry): number {
  return Object.keys(e.diff ?? {}).length
}

const columns: ColumnDef<EntityAuditEntry, unknown>[] = [
  {
    id: 'created_at',
    accessorKey: 'created_at',
    header: 'When',
    cell: ({ row }) => formatDateTime(row.original.created_at),
    enableSorting: true,
    meta: { width: '180px' },
  },
  {
    id: 'action',
    accessorKey: 'action',
    header: 'Action',
    cell: ({ row }) =>
      h(KmChip, {
        size: 'sm',
        tone: actionTone(row.original.action) as never,
        label: row.original.action,
      }),
    enableSorting: true,
    meta: { width: '110px' },
  },
  {
    id: 'actor',
    accessorFn: (e) => e.actor_display || e.actor_type,
    header: 'Actor',
    cell: ({ row }) => {
      const e = row.original
      return h('div', { class: 'stack', 'data-gap': '0' }, [
        h(
          'span',
          { class: 'km-body-2', style: 'word-break: break-all' },
          e.actor_display || e.actor_type,
        ),
        h(
          'span',
          { class: 'km-description text-grey' },
          [e.actor_type, e.source].filter(Boolean).join(' · '),
        ),
      ])
    },
    enableSorting: false,
  },
  {
    id: 'changes',
    accessorFn: diffCount,
    header: 'Changes',
    cell: ({ row }) => {
      const count = diffCount(row.original)
      const paths = Object.keys(row.original.diff ?? {})
        .slice(0, 3)
        .join(', ')
      if (count === 0) return h('span', { class: 'km-description text-grey' }, '—')
      return h('div', { class: 'stack', 'data-gap': '0' }, [
        h('span', { class: 'km-body-2' }, `${count} field${count === 1 ? '' : 's'}`),
        paths
          ? h(
              'span',
              {
                class: 'km-description text-grey font-mono',
                style: 'word-break: break-all',
              },
              count > 3 ? `${paths}, …` : paths,
            )
          : null,
      ])
    },
    enableSorting: true,
    meta: { class: 'km-data-table__td--wrap' },
  },
  {
    id: 'actions',
    header: '',
    cell: () =>
      h('km-glyph', {
        name: 'chevron-right',
        size: '14px',
        tone: 'muted',
      }),
    enableSorting: false,
    meta: { width: '36px' },
  },
]

const { table } = useLocalDataTable<EntityAuditEntry>(entries, columns, {
  defaultSort: [{ id: 'created_at', desc: true }],
  defaultPageSize: 200,
})
</script>

<style scoped>
.entity-audit__diff-table {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.entity-audit__diff-row {
  border: 1px solid var(--ds-color-border, #e0e0e0);
  border-radius: 8px;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.entity-audit__diff-path {
  font-weight: 600;
  word-break: break-all;
}
.entity-audit__snapshot {
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  font-size: 0.8125rem;
  max-block-size: 240px;
  overflow: auto;
}

.entity-audit__unified-diff {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--ds-color-border, #e0e0e0);
  border-radius: 6px;
  overflow: hidden;
  max-block-size: 480px;
  overflow-y: auto;
  background: var(--ds-color-surface-subtle, #fafafa);
  font-size: 0.8125rem;
}
.entity-audit__diff-line {
  display: grid;
  grid-template-columns: 1.25rem 2.5rem 2.5rem 1fr;
  align-items: baseline;
  padding-inline: 0.5rem;
  padding-block: 0.0625rem;
  white-space: pre;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
.entity-audit__diff-line + .entity-audit__diff-line {
  border-block-start: 0 none;
}
.entity-audit__diff-marker {
  font-weight: 700;
  text-align: center;
  user-select: none;
}
.entity-audit__diff-lineno {
  color: var(--ds-color-text-muted, rgba(0, 0, 0, 0.4));
  text-align: end;
  padding-inline-end: 0.5rem;
  user-select: none;
}
.entity-audit__diff-text {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  word-break: break-word;
}
.entity-audit__diff-text--meta {
  color: var(--ds-color-text-muted, rgba(0, 0, 0, 0.55));
  font-style: italic;
}
.entity-audit__diff-line--add {
  background: rgba(76, 175, 80, 0.12);
  color: rgba(27, 94, 32, 1);
}
.entity-audit__diff-line--del {
  background: rgba(244, 67, 54, 0.1);
  color: rgba(183, 28, 28, 1);
}
.entity-audit__diff-line--ctx {
  color: var(--ds-color-text-secondary, rgba(0, 0, 0, 0.7));
}
.entity-audit__diff-line--sep {
  background: var(--ds-color-surface-muted, rgba(0, 0, 0, 0.04));
  color: var(--ds-color-text-muted, rgba(0, 0, 0, 0.55));
}
.entity-audit__snapshot {
  background: var(--ds-color-surface-subtle, #f5f5f5);
  border-radius: 6px;
  padding: 0.5rem;
}

.entity-audit__diff-inline {
  margin-block-start: 0.125rem;
}
.entity-audit__chip {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.125rem 0.5rem;
  border-radius: 6px;
  font-size: 0.8125rem;
  max-inline-size: 100%;
  overflow: hidden;
}
.entity-audit__chip-text {
  white-space: pre-wrap;
  word-break: break-word;
  overflow-wrap: anywhere;
}
.entity-audit__chip--from {
  background: rgba(244, 67, 54, 0.08);
  color: rgba(183, 28, 28, 1);
  border: 1px solid rgba(244, 67, 54, 0.25);
}
.entity-audit__chip--to {
  background: rgba(76, 175, 80, 0.08);
  color: rgba(27, 94, 32, 1);
  border: 1px solid rgba(76, 175, 80, 0.25);
}
.entity-audit__sign {
  font-weight: 700;
  width: 0.75rem;
  text-align: center;
  flex: none;
}

.entity-audit__toggle {
  appearance: none;
  background: none;
  border: none;
  padding: 0.25rem 0;
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  color: var(--ds-color-action-secondary, #2962ff);
  cursor: pointer;
  font-size: 0.875rem;
}
.entity-audit__toggle:hover {
  text-decoration: underline;
}
.entity-audit__snapshots {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}
@media (max-inline-size: 720px) {
  .entity-audit__snapshots {
    grid-template-columns: 1fr;
  }
}
</style>

<style>
/* Row hover affordance — clicking anywhere in the row opens the detail
 * dialog. Scoped style won't reach data-table cells, so we leak the
 * specific selector globally. */
.entity-audit__table tbody tr {
  cursor: pointer;
}
.entity-audit__table tbody tr:hover {
  background: var(--ds-color-surface-hover, rgba(0, 0, 0, 0.03));
}
</style>
