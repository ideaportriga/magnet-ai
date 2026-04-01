/**
 * Frontend → Loki log shipper.
 *
 * Intercepts console.error / console.warn, window.onerror and
 * unhandledrejection, then pushes them to the local Loki instance
 * using the same labels as the backend.
 */

const LOKI_PUSH_URL = '/loki/api/v1/push'

function toNano(ms: number): string {
  return `${ms}000000`
}

function push(severity: string, message: string, extra?: Record<string, unknown>) {
  const payload = extra ? `${message} ${JSON.stringify(extra)}` : message
  const body = {
    streams: [
      {
        stream: {
          application: 'magnet-ai',
          severity,
          logger: 'frontend',
        },
        values: [[toNano(Date.now()), payload]],
      },
    ],
  }

  // fire-and-forget, never throw
  navigator.sendBeacon(
    LOKI_PUSH_URL,
    new Blob([JSON.stringify(body)], { type: 'application/json' }),
  )
}

function safeString(value: unknown): string {
  try {
    if (value === null || value === undefined) return String(value)
    if (typeof value === 'string') return value
    if (value instanceof Error) return value.message
    return JSON.stringify(value)
  } catch {
    return '[unserializable]'
  }
}

export function initLokiLogger() {
  const _error = console.error.bind(console)
  const _warn = console.warn.bind(console)

  console.error = (...args: unknown[]) => {
    _error(...args)
    push('error', args.map(safeString).join(' '))
  }

  console.warn = (...args: unknown[]) => {
    _warn(...args)
    push('warning', args.map(safeString).join(' '))
  }

  window.onerror = (message, source, lineno, colno, error) => {
    push('error', String(message), {
      source,
      lineno,
      colno,
      stack: error?.stack,
    })
    return false // don't suppress default behaviour
  }

  window.addEventListener('unhandledrejection', (event) => {
    const reason = event.reason
    const message =
      reason instanceof Error ? reason.message : String(reason)
    push('error', `Unhandled promise rejection: ${message}`, {
      stack: reason instanceof Error ? reason.stack : undefined,
    })
  })
}
