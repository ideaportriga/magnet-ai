<template>
  <div class="stack full-height" data-gap="md">
    <div class="cluster" data-justify="between" data-align="center" data-wrap="no">
      <div class="km-description text-grey">
        <span v-if="isLoading">{{ m.common_loading() }}</span>
        <span v-else>
          {{ m.audit_entries({ count: entries.length }) }}
        </span>
      </div>
      <km-btn
        flat
        icon="refresh"
        icon-size="14px"
        :label="m.common_refresh()"
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
      :no-records-label="m.audit_noRecords()"
      hide-pagination
      class="entity-audit__table"
      :column-width-vars="tableColumnWidthVars"
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

      <div v-else class="entity-audit__detail stack overflow-auto" data-gap="lg">
        <section class="stack" data-gap="xs">
          <div class="cluster" data-justify="between" data-align="center" data-wrap="no">
            <div class="km-heading-7">
              {{ m.audit_changedFields({ count: diffEntries.length }) }}
            </div>
            <km-input
              v-if="diffEntries.length > 4"
              v-model="diffFilter"
              :placeholder="m.audit_filterByPath()"
              clearable
              dense
              class="entity-audit__filter"
            />
          </div>

          <div v-if="filteredDiffEntries.length === 0" class="km-description text-grey p-md">
            <span v-if="diffEntries.length === 0">{{ m.audit_noFieldChanges() }}</span>
            <span v-else>{{ m.audit_noPathMatches() }}</span>
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
                  :tone="changeKind(change) === 'add' ? 'success' : 'danger'"
                  :label="changeKind(change) === 'add' ? m.audit_added() : m.audit_removed()"
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
          <km-btn
            flat
            :icon="showFullSnapshots ? 'chevron-down' : 'chevron-right'"
            icon-size="12px"
            :label="showFullSnapshots ? m.audit_hideFullState() : m.audit_showFullState()"
            class="entity-audit__toggle"
            @click="showFullSnapshots = !showFullSnapshots"
          />

          <div v-if="showFullSnapshots" class="entity-audit__snapshots">
            <div v-if="detailDetail?.snapshot_before" class="stack" data-gap="2xs">
              <div class="km-description text-grey">{{ m.audit_snapshotBefore() }}</div>
              <pre class="entity-audit__snapshot font-mono">{{ formatValue(detailDetail.snapshot_before) }}</pre>
            </div>
            <div v-if="detailDetail?.snapshot_after" class="stack" data-gap="2xs">
              <div class="km-description text-grey">{{ m.audit_snapshotAfter() }}</div>
              <pre class="entity-audit__snapshot font-mono">{{ formatValue(detailDetail.snapshot_after) }}</pre>
            </div>
          </div>
        </section>
      </div>

      <template #footer>
        <km-btn flat :label="m.common_close()" @click="detailOpen = false" />
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
      :confirm-button-label="m.common_restore()"
      :cancel-button-label="m.common_cancel()"
      notification-icon="warning"
      @confirm="doRestore"
      @cancel="confirmingRestore = false"
    >
      <div class="cluster km-heading-7" data-justify="center">
        {{ m.audit_restoreConfirmTitle() }}
      </div>
      <div class="cluster text-center" data-justify="center">
        {{ m.audit_restoreConfirmBody() }}
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
import KmGlyph from '@ds/components/domain/KmGlyph.vue'
import type { KmGlyphTone } from '@ds/components/domain/KmGlyph.vue'
import { m } from '@/paraglide/messages'
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
const tableColumnWidthVars = {
  '--entity-audit-when-width': '11.25rem',
  '--entity-audit-action-width': '6.875rem',
  '--entity-audit-actions-width': '2.25rem',
}

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
  return action !== 'create' && Boolean(detailEntry.value?.can_restore ?? detailDetail.value?.can_restore)
})

const restoreLabel = computed(() => {
  const action = detailEntry.value?.action
  if (action === 'delete') return m.audit_restoreDeletedEntity()
  return m.audit_restoreThisVersion()
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
    notify.success(m.audit_restored())
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
      err instanceof Error ? err.message : m.audit_restoreFailed(),
    )
  }
}

// ── Table ────────────────────────────────────────────────────────────
function actionTone(action: string): 'success' | 'brand' | 'danger' | 'warning' | 'neutral' {
  switch (action) {
    case 'create':
      return 'success'
    case 'update':
      return 'brand'
    case 'delete':
      return 'danger'
    case 'restore':
      return 'warning'
    default:
      return 'neutral'
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
    header: m.audit_when(),
    cell: ({ row }) => formatDateTime(row.original.created_at),
    enableSorting: true,
    meta: { width: 'var(--entity-audit-when-width)' },
  },
  {
    id: 'action',
    accessorKey: 'action',
    header: m.audit_action(),
    cell: ({ row }) =>
      h(KmChip, {
        size: 'sm',
        tone: actionTone(row.original.action),
        label: row.original.action,
      }),
    enableSorting: true,
    meta: { width: 'var(--entity-audit-action-width)' },
  },
  {
    id: 'actor',
    accessorFn: (e) => e.actor_display || e.actor_type,
    header: m.audit_actor(),
    cell: ({ row }) => {
      const e = row.original
      return h('div', { class: 'stack', 'data-gap': '0' }, [
        h(
          'span',
          { class: 'entity-audit__break-all km-body-2' },
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
    header: m.audit_changes(),
    cell: ({ row }) => {
      const count = diffCount(row.original)
      const paths = Object.keys(row.original.diff ?? {})
        .slice(0, 3)
        .join(', ')
      if (count === 0) return h('span', { class: 'km-description text-grey' }, '—')
      return h('div', { class: 'stack', 'data-gap': '0' }, [
        h('span', { class: 'km-body-2' }, m.audit_fieldCount({ count })),
        paths
          ? h(
              'span',
              {
                class: 'entity-audit__break-all km-description text-grey font-mono',
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
      h(KmGlyph, {
        name: 'chevron-right',
        size: '14px',
        tone: 'muted' as KmGlyphTone,
      }),
    enableSorting: false,
    meta: { width: 'var(--entity-audit-actions-width)' },
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
  gap: var(--ds-space-sm);
}
.entity-audit__table {
  min-block-size: 0;
  flex: 1;
}
.entity-audit__detail {
  min-block-size: 0;
  max-block-size: 70vh;
}
.entity-audit__filter {
  max-inline-size: 15rem;
}
.entity-audit__diff-row {
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-lg);
  padding: var(--ds-space-md);
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-sm);
}
.entity-audit__diff-path {
  font-weight: 600;
  word-break: break-all;
}
.entity-audit__snapshot {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  margin: 0;
  font-size: var(--ds-font-size-md);
  max-block-size: 15rem;
  overflow: auto;
}

.entity-audit__unified-diff {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
  overflow: hidden;
  max-block-size: 30rem;
  overflow-y: auto;
  background: var(--ds-color-surface-sunken);
  font-size: var(--ds-font-size-md);
}
.entity-audit__diff-line {
  display: grid;
  grid-template-columns: 1.25rem 2.5rem 2.5rem 1fr;
  align-items: baseline;
  padding-inline: var(--ds-space-sm);
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
  color: var(--ds-color-fg-muted);
  text-align: end;
  padding-inline-end: var(--ds-space-sm);
  user-select: none;
}
.entity-audit__diff-text {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.entity-audit__diff-text--meta {
  color: var(--ds-color-fg-muted);
  font-style: italic;
}
.entity-audit__diff-line--add {
  background: var(--ds-color-success-soft);
  color: var(--ds-color-success-on-soft);
}
.entity-audit__diff-line--del {
  background: var(--ds-color-danger-soft);
  color: var(--ds-color-danger-on-soft);
}
.entity-audit__diff-line--ctx {
  color: var(--ds-color-fg-muted);
}
.entity-audit__diff-line--sep {
  background: var(--ds-color-surface);
  color: var(--ds-color-fg-muted);
}
.entity-audit__snapshot {
  background: var(--ds-color-surface-sunken);
  border-radius: var(--ds-radius-md);
  padding: var(--ds-space-sm);
}

.entity-audit__diff-inline {
  margin-block-start: var(--ds-space-2xs);
}
.entity-audit__chip {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-xs);
  padding: var(--ds-space-2xs) var(--ds-space-sm);
  border-radius: var(--ds-radius-md);
  font-size: var(--ds-font-size-md);
  max-inline-size: 100%;
  overflow: hidden;
}
.entity-audit__chip-text {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.entity-audit__chip--from {
  background: var(--ds-color-danger-soft);
  color: var(--ds-color-danger-on-soft);
  border: 1px solid var(--ds-color-danger-solid);
}
.entity-audit__chip--to {
  background: var(--ds-color-success-soft);
  color: var(--ds-color-success-on-soft);
  border: 1px solid var(--ds-color-success-solid);
}
.entity-audit__sign {
  font-weight: 700;
  inline-size: var(--ds-space-md);
  text-align: center;
  flex: none;
}

.entity-audit__toggle {
  align-self: flex-start;
}
.entity-audit__snapshots {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--ds-space-md);
}
@media (width <= 45rem) {
  .entity-audit__snapshots {
    grid-template-columns: 1fr;
  }
}
.entity-audit__break-all {
  word-break: break-all;
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
  background: var(--ds-color-table-hover);
}
</style>
