import { Notify } from 'quasar'

export interface NotifyConfirmOptions {
  message: string
  onConfirm: () => void
  confirmLabel?: string
  cancelLabel?: string
  onCancel?: () => void
}

export const notify = {
  success: (message: string) =>
    Notify.create({
      message,
      icon: 'check_circle',
      color: 'green-9',
      textColor: 'white',
      timeout: 2500,
      group: 'success',
    }),

  error: (message: string) =>
    Notify.create({
      message,
      icon: 'error',
      color: 'red-9',
      textColor: 'white',
      timeout: 5000,
      group: 'error',
    }),

  warning: (message: string) =>
    Notify.create({
      message,
      icon: 'warning',
      color: 'orange-9',
      textColor: 'white',
      timeout: 3000,
      group: 'warning',
    }),

  info: (message: string) =>
    Notify.create({
      message,
      icon: 'info',
      color: 'blue-grey-8',
      textColor: 'white',
      timeout: 2000,
      group: 'info',
    }),

  /** Pass translated string: notify.copied(m.common_copiedToClipboard()) */
  copied: (message = 'Copied to clipboard') =>
    Notify.create({
      message,
      icon: 'content_copy',
      color: 'grey-9',
      textColor: 'white',
      timeout: 1000,
      group: 'copied',
    }),

  /**
   * Sticky red toast with Confirm/Cancel buttons — used for destructive
   * actions (delete variant, delete entity). Prefer a proper modal when
   * possible; this exists for parity with the legacy $q.notify-confirm pattern.
   */
  confirm: ({ message, onConfirm, onCancel, confirmLabel = 'Confirm', cancelLabel = 'Cancel' }: NotifyConfirmOptions) =>
    Notify.create({
      message,
      color: 'red-9',
      textColor: 'white',
      icon: 'error',
      group: 'error',
      timeout: 0,
      actions: [
        { label: cancelLabel, color: 'yellow', handler: () => onCancel?.() },
        { label: confirmLabel, color: 'white', handler: () => onConfirm() },
      ],
    }),
}
