import { useQuasar } from 'quasar'

type NotifyTone = 'success' | 'warning' | 'error'

const STYLE: Record<NotifyTone, { color: string; textColor: string; timeout: number }> = {
  success: { color: 'positive', textColor: 'black', timeout: 1000 },
  warning: { color: 'warning', textColor: 'black', timeout: 2000 },
  error: { color: 'negative', textColor: 'white', timeout: 3000 },
}

/** Toasts in the admin's usual style; call from `setup`. */
export function useModelNotify() {
  const $q = useQuasar()
  return (tone: NotifyTone, message: string) => $q.notify({ position: 'top', message, ...STYLE[tone] })
}
