/**
 * `useDialog` — programmatic confirm/alert API.
 *
 *   const dialog = useDialog()
 *   const ok = await dialog.confirm({
 *     title: 'Delete?',
 *     description: 'This cannot be undone.',
 *     tone: 'danger',
 *   })
 */

import { pushConfirm, type DialogConfirmOptions } from '../hosts/dialogStore'

export function useDialog() {
  return {
    /** Returns a Promise that resolves to `true` (Confirm) or `false` (Cancel/Esc). */
    confirm: (options: DialogConfirmOptions): Promise<boolean> => pushConfirm(options),
  }
}

export type { DialogConfirmOptions } from '../hosts/dialogStore'
