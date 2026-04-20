import { notify } from '@shared/utils/notify'

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
