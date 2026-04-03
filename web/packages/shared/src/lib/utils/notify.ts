import { Notify } from 'quasar'

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
}
