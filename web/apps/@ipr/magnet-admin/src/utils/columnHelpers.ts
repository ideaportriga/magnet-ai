import { h, resolveComponent, type Component } from 'vue'
import { createColumnHelper, type ColumnDef, type Table, type Row } from '@tanstack/vue-table'
import { formatDateTime } from '@shared/utils'
import type { BaseEntity } from '@/types'

/**
 * Column meta for km-data-table rendering
 */
export interface KmColumnMeta {
  align?: 'left' | 'center' | 'right'
  class?: string
  width?: string
  /** Backend field name for server-side sorting (when column id differs from DB field) */
  sortField?: string
}

/**
 * Typed column helper factory for an entity type
 */
export function createColumns<T extends BaseEntity>() {
  return createColumnHelper<T>()
}

/**
 * Simple text column
 */
export function textColumn<T extends BaseEntity>(
  id: string & keyof T,
  header: string,
  options?: {
    sortable?: boolean
    align?: 'left' | 'center' | 'right'
    format?: (val: unknown) => string
    width?: string
  },
): ColumnDef<T, unknown> {
  return {
    id,
    accessorKey: id,
    header,
    cell: ({ getValue }) => {
      const val = getValue()
      if (options?.format) return options.format(val)
      return val != null && val !== '' ? String(val) : '-'
    },
    enableSorting: options?.sortable ?? true,
    meta: {
      align: options?.align ?? 'left',
      width: options?.width,
    } as KmColumnMeta,
  }
}

/**
 * Date column with automatic formatting
 */
export function dateColumn<T extends BaseEntity>(
  id: string & keyof T,
  header: string,
  options?: { sortable?: boolean; align?: 'left' | 'center' | 'right' },
): ColumnDef<T, unknown> {
  return {
    id,
    accessorKey: id,
    header,
    cell: ({ getValue }) => {
      const val = getValue()
      return val ? formatDateTime(val as string) : '-'
    },
    enableSorting: options?.sortable ?? true,
    meta: {
      align: options?.align ?? 'left',
    } as KmColumnMeta,
  }
}

/**
 * Column that renders a Vue component, passing the full row as prop
 */
export function componentColumn<T extends BaseEntity>(
  id: string,
  header: string,
  component: Component,
  options?: {
    accessorKey?: string
    sortable?: boolean
    align?: 'left' | 'center' | 'right'
    sortFn?: (a: T, b: T) => number
    props?: (row: T) => Record<string, unknown>
  },
): ColumnDef<T, unknown> {
  return {
    id,
    ...(options?.accessorKey ? { accessorKey: options.accessorKey } : { accessorFn: () => null }),
    header,
    cell: ({ row }) => {
      const extraProps = options?.props ? options.props(row.original) : {}
      return h(component, { row: row.original, ...extraProps })
    },
    enableSorting: options?.sortable ?? false,
    ...(options?.sortFn ? { sortingFn: (a, b) => options.sortFn!(a.original, b.original) } : {}),
    meta: {
      align: options?.align ?? 'left',
    } as KmColumnMeta,
  }
}

/**
 * System name column with copy-chip rendering
 * Uses km-chip-copy component (globally registered)
 */
export function chipCopyColumn<T extends BaseEntity>(
  header = 'System Name',
  options?: { id?: string; accessorKey?: string },
): ColumnDef<T, unknown> {
  return {
    id: options?.id ?? 'system_name',
    accessorKey: options?.accessorKey ?? 'system_name',
    header,
    cell: ({ getValue }) => {
      const val = getValue()
      if (!val) return '-'
      const KmChipCopy = resolveComponent('km-chip-copy')
      return h(KmChipCopy, { label: String(val) })
    },
    enableSorting: true,
    meta: { align: 'left' } as KmColumnMeta,
  }
}

/**
 * Name + Description column — renders name as title and description below it
 */
export function nameDescriptionColumn<T extends BaseEntity>(
  header = 'Name',
  options?: { sortable?: boolean; width?: string },
): ColumnDef<T, unknown> {
  return {
    id: 'nameDescription',
    accessorKey: 'name',
    header,
    cell: ({ row }) => {
      const name = (row.original as Record<string, unknown>).name as string ?? ''
      const description = (row.original as Record<string, unknown>).description as string ?? ''
      return h('div', {}, [
        h('div', { class: 'km-title text-left ellipsis' }, name),
        h('div', { class: 'km-field text-left ellipsis' }, description),
      ])
    },
    enableSorting: options?.sortable ?? true,
    meta: { align: 'left', width: options?.width, sortField: 'name' } as KmColumnMeta,
  }
}

/**
 * Action/drilldown column — chevron button
 */
export function drilldownColumn<T extends BaseEntity>(
  id = 'drilldown',
): ColumnDef<T, unknown> {
  return {
    id,
    accessorFn: () => null,
    header: '',
    cell: () => {
      const QIcon = resolveComponent('q-icon')
      return h(QIcon, { name: 'chevron_right', size: '20px', class: 'text-grey-6' })
    },
    enableSorting: false,
    meta: { align: 'center', width: '40px' } as KmColumnMeta,
  }
}

/**
 * Checkbox column for multi-row selection.
 * Requires `enableRowSelection: true` in useLocalDataTable options.
 */
export function selectionColumn<T extends BaseEntity>(): ColumnDef<T, unknown> {
  return {
    id: '_select',
    header: ({ table }: { table: Table<T> }) => {
      const QCheckbox = resolveComponent('q-checkbox')
      return h(QCheckbox, {
        modelValue: table.getIsAllRowsSelected(),
        indeterminate: table.getIsSomeRowsSelected() && !table.getIsAllRowsSelected(),
        'onUpdate:modelValue': () => table.toggleAllRowsSelected(),
        dense: true,
        size: 'sm',
        color: 'primary',
        class: 'selection-checkbox',
      })
    },
    cell: ({ row }: { row: Row<T> }) => {
      const QCheckbox = resolveComponent('q-checkbox')
      return h(QCheckbox, {
        modelValue: row.getIsSelected(),
        'onUpdate:modelValue': () => row.toggleSelected(),
        dense: true,
        size: 'sm',
        color: 'primary',
        onClick: (e: Event) => e.stopPropagation(),
        class: 'selection-checkbox',
      })
    },
    enableSorting: false,
    meta: { align: 'center', width: '40px' } as KmColumnMeta,
  }
}
