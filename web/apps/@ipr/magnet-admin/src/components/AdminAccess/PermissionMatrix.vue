<!--
  Resource × action permission grid built on TanStack Table.

  Rows are resource types (agents, prompts, collections, …).
  Columns are the distinct actions found in the catalog (read, write,
  delete, execute, share, manage). Cells are checkboxes when the action
  exists for that resource, em-dashes otherwise. Column headers double
  as “toggle the whole column” buttons.

  Capability ceiling preserved: an actor can only grant codes they
  themselves hold. Superuser bypasses. Already-selected codes stay
  enabled so the user can always *clear* a grant.

  `readonly` mode disables every checkbox + headers (used for system
  roles, which the backend refuses to mutate).
-->
<template>
  <div class="stack" data-gap="sm">
    <div class="cluster" data-align="center" data-gap="sm" data-wrap="yes">
      <km-input
        data-test="permission-search"
        placeholder="Filter by resource"
        icon-before="search"
        :model-value="globalFilter"
        clearable
        style="max-inline-size: 280px"
        @input="onSearchInput"
      />
      <div class="km-space" />
      <span class="km-description text-grey">
        {{ selectedCount }} of {{ totalCount }} permission{{ totalCount === 1 ? '' : 's' }} granted
      </span>
      <km-btn
        flat
        :disabled="readonly || selectedCount === 0"
        label="Clear all"
        @click="clearAll"
      />
      <km-btn
        flat
        :disabled="readonly || allEligibleSelected"
        label="Select all (allowed)"
        @click="selectAllEligible"
      />
    </div>

    <km-data-table
      :table="table"
      :loading="false"
      fill-height
      row-key="resource"
      no-records-label="No resources match the filter."
      hide-pagination
    />
  </div>
</template>

<script setup lang="ts">
import { computed, h } from 'vue'
import type { ColumnDef, HeaderContext, CellContext } from '@tanstack/vue-table'
import { usePermissions } from '@shared'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import type { PermissionEntry } from '@/api/adminAccess'
import KmCheckbox from '@ds/components/domain/KmCheckbox.vue'
import KmChip from '@ds/components/domain/KmChip.vue'

const props = defineProps<{
  catalog: PermissionEntry[]
  /** Currently selected permission codes. */
  modelValue: string[]
  /** Hide the controls and disable toggling (used for system roles). */
  readonly?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', codes: string[]): void
}>()

const { can, isSuperuser } = usePermissions()

const selected = computed(() => new Set(props.modelValue))

// ── Catalog → matrix ──────────────────────────────────────────────────
/** Per resource: action → entry mapping. */
interface MatrixRow {
  resource: string
  entries: Map<string, PermissionEntry>
}

const matrixRows = computed<MatrixRow[]>(() => {
  const byResource = new Map<string, Map<string, PermissionEntry>>()
  for (const entry of props.catalog) {
    let actions = byResource.get(entry.resource_type)
    if (!actions) {
      actions = new Map()
      byResource.set(entry.resource_type, actions)
    }
    actions.set(entry.action, entry)
  }
  return Array.from(byResource.entries())
    .map(([resource, entries]) => ({ resource, entries }))
    .sort((a, b) => a.resource.localeCompare(b.resource))
})

/** Stable, sorted list of distinct actions across the whole catalog. */
const allActions = computed<string[]>(() => {
  const set = new Set<string>()
  for (const e of props.catalog) set.add(e.action)
  // Conventional order first, anything else after.
  const conventional = ['read', 'write', 'delete', 'execute', 'share', 'manage']
  const ordered: string[] = []
  for (const a of conventional) {
    if (set.has(a)) {
      ordered.push(a)
      set.delete(a)
    }
  }
  return ordered.concat(Array.from(set).sort())
})

const totalCount = computed(() => props.catalog.length)
const selectedCount = computed(() => {
  let n = 0
  for (const code of selected.value) {
    // Only count codes that exist in the catalog (defensive).
    if (props.catalog.some((e) => e.code === code)) n++
  }
  return n
})

// ── Capability ceiling ────────────────────────────────────────────────

function entryDisabled(entry: PermissionEntry): boolean {
  if (props.readonly) return true
  if (isSuperuser.value) return false
  if (selected.value.has(entry.code)) return false
  return !can(entry.code)
}

// ── Mutations ─────────────────────────────────────────────────────────

function toggle(entry: PermissionEntry) {
  if (entryDisabled(entry)) return
  const next = new Set(selected.value)
  if (next.has(entry.code)) next.delete(entry.code)
  else next.add(entry.code)
  emit('update:modelValue', Array.from(next).sort())
}

function toggleResource(row: MatrixRow) {
  if (props.readonly) return
  // If every eligible entry in the row is selected → clear; else add all
  // eligible. "Eligible" honours capability ceiling.
  const eligible = Array.from(row.entries.values()).filter((e) => !entryDisabled(e) || selected.value.has(e.code))
  const allOn = eligible.every((e) => selected.value.has(e.code))
  const next = new Set(selected.value)
  if (allOn) {
    for (const e of eligible) next.delete(e.code)
  } else {
    for (const e of eligible) {
      if (!entryDisabled(e)) next.add(e.code)
    }
  }
  emit('update:modelValue', Array.from(next).sort())
}

function toggleAction(action: string) {
  if (props.readonly) return
  const acrossRows = matrixRows.value
    .map((r) => r.entries.get(action))
    .filter((e): e is PermissionEntry => e !== undefined)
  const eligible = acrossRows.filter((e) => !entryDisabled(e) || selected.value.has(e.code))
  const allOn = eligible.every((e) => selected.value.has(e.code))
  const next = new Set(selected.value)
  if (allOn) {
    for (const e of eligible) next.delete(e.code)
  } else {
    for (const e of eligible) {
      if (!entryDisabled(e)) next.add(e.code)
    }
  }
  emit('update:modelValue', Array.from(next).sort())
}

function clearAll() {
  if (props.readonly) return
  // Drop only codes that are present in the catalog AND currently selected
  // AND that the actor is allowed to drop. With our model, any selected
  // code can be cleared by anyone with `write:roles` — capability ceiling
  // only restricts *granting* new codes.
  const next = new Set(selected.value)
  for (const e of props.catalog) next.delete(e.code)
  emit('update:modelValue', Array.from(next).sort())
}

function selectAllEligible() {
  if (props.readonly) return
  const next = new Set(selected.value)
  for (const e of props.catalog) {
    if (!entryDisabled(e)) next.add(e.code)
  }
  emit('update:modelValue', Array.from(next).sort())
}

const allEligibleSelected = computed(() =>
  props.catalog.every((e) => entryDisabled(e) || selected.value.has(e.code)),
)

// ── Column header state ───────────────────────────────────────────────

interface ColumnHeaderState {
  selectedOf: number
  totalOf: number
  allOn: boolean
  anyOn: boolean
  hasEligible: boolean
}

function columnState(action: string): ColumnHeaderState {
  let total = 0
  let on = 0
  let eligible = 0
  for (const row of matrixRows.value) {
    const entry = row.entries.get(action)
    if (!entry) continue
    total++
    if (selected.value.has(entry.code)) on++
    if (!entryDisabled(entry) || selected.value.has(entry.code)) eligible++
  }
  return {
    selectedOf: on,
    totalOf: total,
    allOn: total > 0 && on === total,
    anyOn: on > 0,
    hasEligible: eligible > 0,
  }
}

// ── Helpers ───────────────────────────────────────────────────────────

function formatResource(resource: string): string {
  return resource.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

function rowSelectedCount(row: MatrixRow): number {
  let n = 0
  for (const e of row.entries.values()) {
    if (selected.value.has(e.code)) n++
  }
  return n
}

// ── Columns ───────────────────────────────────────────────────────────

const columns = computed<ColumnDef<MatrixRow, unknown>[]>(() => {
  const cols: ColumnDef<MatrixRow, unknown>[] = [
    {
      id: 'resource',
      accessorKey: 'resource',
      header: 'Resource',
      cell: ({ row }: CellContext<MatrixRow, unknown>) => {
        const r = row.original
        const granted = rowSelectedCount(r)
        const total = r.entries.size
        return h(
          'button',
          {
            type: 'button',
            class: 'permission-matrix__row-toggle',
            disabled: props.readonly,
            onClick: (e: Event) => {
              e.stopPropagation()
              toggleResource(r)
            },
          },
          [
            h('span', { class: 'km-title' }, formatResource(r.resource)),
            h(KmChip, {
              size: 'sm',
              tone: granted === total && total > 0 ? 'brand' : 'muted',
              label: `${granted}/${total}`,
            }),
          ],
        )
      },
      enableSorting: true,
      meta: { width: '240px' },
    },
  ]

  for (const action of allActions.value) {
    cols.push({
      id: `action:${action}`,
      accessorFn: (r) => (r.entries.has(action) ? (selected.value.has(r.entries.get(action)!.code) ? 1 : 0) : -1),
      header: (ctx: HeaderContext<MatrixRow, unknown>) => {
        const state = columnState(action)
        return h(
          'button',
          {
            type: 'button',
            class: 'permission-matrix__col-toggle',
            disabled: props.readonly || !state.hasEligible,
            'aria-label': `Toggle ${action} for all resources`,
            'data-test': `column-toggle-${action}`,
            onClick: (e: Event) => {
              e.stopPropagation()
              toggleAction(action)
            },
          },
          [
            h('span', { class: 'permission-matrix__col-name' }, action),
            h(KmChip, {
              size: 'sm',
              tone: state.allOn ? 'brand' : state.anyOn ? 'warning' : 'muted',
              label: `${state.selectedOf}/${state.totalOf}`,
            }),
          ],
        )
      },
      cell: ({ row }: CellContext<MatrixRow, unknown>) => {
        const entry = row.original.entries.get(action)
        if (!entry) {
          return h('span', { class: 'permission-matrix__dash' }, '—')
        }
        const isOn = selected.value.has(entry.code)
        const disabled = entryDisabled(entry)
        return h(
          'div',
          {
            class: 'permission-matrix__cell',
            title: entry.description
              ? `${entry.code} — ${entry.description}`
              : entry.code,
          },
          [
            h(KmCheckbox, {
              modelValue: isOn,
              disable: disabled,
              size: '20px',
              'data-test': `permission-toggle-${entry.code}`,
              'onUpdate:modelValue': () => toggle(entry),
            }),
          ],
        )
      },
      enableSorting: true,
      meta: { align: 'center', width: '120px' },
    })
  }

  return cols
})

const { table, globalFilter } = useLocalDataTable<MatrixRow>(matrixRows, columns, {
  defaultSort: [{ id: 'resource', desc: false }],
  defaultPageSize: 200,
})

function onSearchInput(val: string) {
  globalFilter.value = val
}
</script>

<style scoped>
.permission-matrix__row-toggle {
  background: transparent;
  border: none;
  padding: 0;
  display: flex;
  align-items: center;
  gap: var(--ds-space-sm, 8px);
  cursor: pointer;
  text-align: left;
  inline-size: 100%;
}
.permission-matrix__row-toggle:disabled {
  cursor: default;
  opacity: 0.85;
}

.permission-matrix__col-toggle {
  background: transparent;
  border: none;
  padding: 0;
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-xs, 4px);
  cursor: pointer;
  text-transform: lowercase;
  font-weight: 600;
}
.permission-matrix__col-toggle:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}
.permission-matrix__col-name {
  font-family: var(--ds-font-mono, monospace);
  font-size: 0.85rem;
}

.permission-matrix__cell {
  display: flex;
  justify-content: center;
  align-items: center;
}

.permission-matrix__dash {
  color: var(--ds-color-gray-400, #c0c0c0);
}
</style>
