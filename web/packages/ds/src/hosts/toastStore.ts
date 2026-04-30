/**
 * Module-level reactive toast queue. Lives outside any Pinia/Vue plugin so
 * `useNotify()` can be called from anywhere (router guards, store actions,
 * non-component code) without a setup() context.
 *
 * `DsToastHost` subscribes to this queue and renders each item via Reka UI
 * `ToastRoot`. The host is mounted once at the app root (see
 * `magnet-admin/App.vue`).
 */

import { reactive, readonly } from 'vue'

export type ToastTone = 'success' | 'error' | 'warning' | 'info' | 'copied' | 'confirm' | 'neutral'

export interface ToastAction {
  label: string
  /** Called when the user activates the action. The toast is dismissed afterwards. */
  onClick: () => void
  variant?: 'primary' | 'secondary'
}

export interface ToastItem {
  id: string
  tone: ToastTone
  message: string
  /** ms before auto-dismiss. `0` means sticky (no auto-dismiss). */
  duration: number
  /** Optional rich content; takes precedence over `message` when set. */
  description?: string
  /** Optional buttons (e.g. confirm/cancel for destructive actions). */
  actions?: ToastAction[]
  /** Callback invoked once the toast leaves the queue regardless of how. */
  onDismiss?: () => void
}

export interface ToastInput extends Omit<Partial<ToastItem>, 'id' | 'tone' | 'message'> {
  tone: ToastTone
  message: string
}

interface ToastStoreState {
  items: ToastItem[]
}

const state = reactive<ToastStoreState>({ items: [] })

const DEFAULT_DURATION_BY_TONE: Record<ToastTone, number> = {
  success: 2500,
  error: 5000,
  warning: 3000,
  info: 2000,
  copied: 1000,
  confirm: 0,
  neutral: 3000,
}

function nextId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID()
  }
  return `toast-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

export function pushToast(input: ToastInput): { id: string; dismiss: () => void } {
  const item: ToastItem = {
    id: nextId(),
    duration: DEFAULT_DURATION_BY_TONE[input.tone],
    ...input,
  }
  state.items.push(item)
  return { id: item.id, dismiss: () => dismissToast(item.id) }
}

export function dismissToast(id: string): void {
  const idx = state.items.findIndex((t) => t.id === id)
  if (idx === -1) return
  const [removed] = state.items.splice(idx, 1)
  removed?.onDismiss?.()
}

export function clearToasts(): void {
  while (state.items.length) {
    const [removed] = state.items.splice(0, 1)
    removed?.onDismiss?.()
  }
}

/** Read-only view of the queue, exposed for the host component. */
export const toastQueue = readonly(state) as Readonly<ToastStoreState>
