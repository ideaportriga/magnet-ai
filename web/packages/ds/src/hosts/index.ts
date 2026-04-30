/**
 * @ds hosts barrel.
 *
 * Mount the host components once at the application root — they own the
 * Portal targets and shared queues for `useNotify`, `useDialog`, `useLoading`.
 */

import DsToastHost from './DsToastHost.vue'
import DsDialogHost from './DsDialogHost.vue'
import DsLoadingHost from './DsLoadingHost.vue'

export { DsToastHost, DsDialogHost, DsLoadingHost }

export {
  pushToast,
  dismissToast,
  clearToasts,
  toastQueue,
  type ToastInput,
  type ToastItem,
  type ToastTone,
  type ToastAction,
} from './toastStore'

export {
  pushConfirm,
  settleConfirm,
  dialogQueue,
  type DialogConfirmOptions,
  type DialogConfirmItem,
} from './dialogStore'

export {
  showLoading,
  clearLoading,
  loadingState,
  type LoadingShowOptions,
} from './loadingStore'
