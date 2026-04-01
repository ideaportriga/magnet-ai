import { useQuasar } from 'quasar'

export function useNotify() {
  const $q = useQuasar()

  return {
    notifySuccess: (message: string) =>
      $q.notify({
        message,
        icon: 'check_circle',
        color: 'green-9',
        textColor: 'white',
        timeout: 2500,
        group: 'success',
      }),

    notifyError: (message: string) =>
      $q.notify({
        message,
        icon: 'error',
        color: 'red-9',
        textColor: 'white',
        timeout: 5000,
        group: 'error',
      }),

    notifyWarning: (message: string) =>
      $q.notify({
        message,
        icon: 'warning',
        color: 'orange-9',
        textColor: 'white',
        timeout: 3000,
        group: 'warning',
      }),

    notifyInfo: (message: string) =>
      $q.notify({
        message,
        icon: 'info',
        color: 'blue-grey-8',
        textColor: 'white',
        timeout: 2000,
        group: 'info',
      }),

    notifyCopied: (message = 'Copied') =>
      $q.notify({
        message,
        icon: 'content_copy',
        color: 'grey-9',
        textColor: 'white',
        timeout: 1000,
        group: 'copied',
      }),
  }
}
