/**
 * `useNotify` — toast composable matching the legacy `@shared/utils/notify`
 * surface so the codemod step can swap the import without touching call
 * sites.
 *
 * Methods (same as today):
 *
 *   notify.success(message)
 *   notify.error(message)
 *   notify.warning(message)
 *   notify.info(message)
 *   notify.copied(message?)
 *   notify.confirm({ message, onConfirm, onCancel?, confirmLabel?, cancelLabel? })
 *
 * Each call returns `{ id, dismiss }` so callers can dismiss programmatically.
 */

import { pushToast, type ToastAction } from '../hosts/toastStore'

export interface NotifyConfirmOptions {
  message: string
  onConfirm: () => void
  confirmLabel?: string
  cancelLabel?: string
  onCancel?: () => void
}

export interface NotifyHandle {
  id: string
  dismiss: () => void
}

const success = (message: string): NotifyHandle => pushToast({ tone: 'success', message })
const error = (message: string): NotifyHandle => pushToast({ tone: 'error', message })
const warning = (message: string): NotifyHandle => pushToast({ tone: 'warning', message })
const info = (message: string): NotifyHandle => pushToast({ tone: 'info', message })
const copied = (message = 'Copied to clipboard'): NotifyHandle => pushToast({ tone: 'copied', message })

const confirm = ({
  message,
  onConfirm,
  onCancel,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
}: NotifyConfirmOptions): NotifyHandle => {
  const actions: ToastAction[] = [
    { label: cancelLabel, variant: 'secondary', onClick: () => onCancel?.() },
    { label: confirmLabel, variant: 'primary', onClick: () => onConfirm() },
  ]
  return pushToast({ tone: 'confirm', message, actions, duration: 0 })
}

/**
 * Singleton notify object. Identical shape to `@shared/utils/notify` exported
 * by the legacy code path so consumers can switch via re-export.
 */
export const notify = {
  success,
  error,
  warning,
  info,
  copied,
  confirm,
}

/**
 * Composable wrapper that mirrors the existing
 * `magnet-admin/src/composables/useNotify.ts` shape so the in-app composable
 * can become a thin re-export.
 */
export function useNotify() {
  return {
    notifySuccess: notify.success,
    notifyError: notify.error,
    notifyWarning: notify.warning,
    notifyInfo: notify.info,
    notifyCopied: notify.copied,
    notifyConfirm: notify.confirm,
  }
}
