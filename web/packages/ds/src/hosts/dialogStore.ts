/**
 * Programmatic dialog queue. Each entry is a confirmation/info dialog with
 * promise-based resolution — replaces Quasar's `Dialog.create({ ... })
 * .onOk(...).onCancel(...)` chain.
 *
 *   const ok = await dialogStore.confirm({
 *     title: 'Delete user?',
 *     description: 'This cannot be undone.',
 *     tone: 'danger',
 *   })
 *
 * Visible items are rendered by `DsDialogHost`.
 */

import { reactive, readonly } from 'vue'

export interface DialogConfirmOptions {
  title: string
  description?: string
  confirmLabel?: string
  cancelLabel?: string
  tone?: 'neutral' | 'danger'
}

export interface DialogConfirmItem extends DialogConfirmOptions {
  id: string
  open: boolean
  resolve: (confirmed: boolean) => void
}

interface DialogState {
  items: DialogConfirmItem[]
}

const state = reactive<DialogState>({ items: [] })

function nextId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID()
  }
  return `dialog-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

export function pushConfirm(options: DialogConfirmOptions): Promise<boolean> {
  return new Promise<boolean>((resolve) => {
    state.items.push({ id: nextId(), open: true, resolve, ...options })
  })
}

export function settleConfirm(id: string, confirmed: boolean): void {
  const item = state.items.find((i) => i.id === id)
  if (!item) return
  item.open = false
  item.resolve(confirmed)
  // Remove on the next tick to allow exit transitions to play.
  queueMicrotask(() => {
    const idx = state.items.findIndex((i) => i.id === id)
    if (idx !== -1) state.items.splice(idx, 1)
  })
}

export const dialogQueue = readonly(state) as Readonly<DialogState>
