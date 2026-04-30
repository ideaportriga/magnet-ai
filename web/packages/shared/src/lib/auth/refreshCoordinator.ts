const refreshPromises = new Map<string, Promise<boolean>>()

const LOCK_KEY_PREFIX = 'magnet-ai:auth-refresh-lock'
const RESULT_KEY_PREFIX = 'magnet-ai:auth-refresh-result'
const WEB_LOCK_PREFIX = 'magnet-ai:auth-refresh'
const LOCK_TTL_MS = 10_000
const WAIT_TIMEOUT_MS = 12_000
const POLL_INTERVAL_MS = 100
const RETRY_BASE_DELAY_MS = 300
const RETRY_MAX_DELAY_MS = 2_000
const RETRY_ATTEMPTS = 3
const RETRYABLE_REFRESH_STATUSES = new Set([409, 423])
const instanceId = createInstanceId()

interface RefreshLockRecord {
  ownerId: string
  createdAt: number
  expiresAt: number
}

interface RefreshResultRecord {
  ownerId: string
  ok: boolean
  completedAt: number
}

function authBaseKey(baseUrl: string): string {
  return baseUrl.replace(/\/$/, '')
}

function refreshUrl(baseUrl: string): string {
  return `${authBaseKey(baseUrl)}/api/v2/auth/refresh`
}

async function doRefresh(baseUrl: string): Promise<boolean> {
  try {
    for (let attempt = 0; attempt <= RETRY_ATTEMPTS; attempt += 1) {
      const res = await fetch(refreshUrl(baseUrl), {
        method: 'POST',
        credentials: 'include',
      })
      if (res.ok) return true
      if (!RETRYABLE_REFRESH_STATUSES.has(res.status) || attempt === RETRY_ATTEMPTS) return false
      await delay(retryDelayFor(res, attempt))
    }
    return false
  } catch {
    return false
  }
}

function retryDelayFor(res: Response, attempt: number): number {
  const serverDelay = parseRetryAfter(res.headers.get('Retry-After'))
  if (serverDelay !== null) return Math.min(serverDelay, RETRY_MAX_DELAY_MS)
  const backoff = RETRY_BASE_DELAY_MS * Math.pow(2, attempt)
  return Math.min(backoff, RETRY_MAX_DELAY_MS)
}

function parseRetryAfter(value: string | null): number | null {
  if (!value) return null
  const seconds = Number(value)
  if (Number.isFinite(seconds) && seconds >= 0) return Math.round(seconds * 1000)
  const date = Date.parse(value)
  if (Number.isFinite(date)) return Math.max(0, date - Date.now())
  return null
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    globalThis.setTimeout(resolve, ms)
  })
}

function createInstanceId(): string {
  if (typeof globalThis.crypto?.randomUUID === 'function') {
    return globalThis.crypto.randomUUID()
  }

  return `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

function createOwnerId(): string {
  return `${instanceId}:${Date.now()}:${Math.random().toString(36).slice(2)}`
}

function storageKey(prefix: string, key: string): string {
  return `${prefix}:${key}`
}

function getRefreshStorage(): Storage | null {
  if (typeof window === 'undefined') return null

  try {
    return window.localStorage
  } catch {
    return null
  }
}

function parseLockRecord(value: string | null): RefreshLockRecord | null {
  if (!value) return null

  try {
    const parsed = JSON.parse(value) as Partial<RefreshLockRecord>
    if (typeof parsed.ownerId !== 'string') return null
    if (typeof parsed.createdAt !== 'number') return null
    if (typeof parsed.expiresAt !== 'number') return null
    return parsed as RefreshLockRecord
  } catch {
    return null
  }
}

function parseResultRecord(value: string | null): RefreshResultRecord | null {
  if (!value) return null

  try {
    const parsed = JSON.parse(value) as Partial<RefreshResultRecord>
    if (typeof parsed.ownerId !== 'string') return null
    if (typeof parsed.ok !== 'boolean') return null
    if (typeof parsed.completedAt !== 'number') return null
    return parsed as RefreshResultRecord
  } catch {
    return null
  }
}

function tryAcquireRefreshLock(storage: Storage, lockKey: string, ownerId: string): RefreshLockRecord | null {
  const now = Date.now()
  const currentLock = parseLockRecord(storage.getItem(lockKey))
  if (currentLock && currentLock.expiresAt > now && currentLock.ownerId !== ownerId) return null

  const nextLock: RefreshLockRecord = {
    ownerId,
    createdAt: now,
    expiresAt: now + LOCK_TTL_MS,
  }

  storage.setItem(lockKey, JSON.stringify(nextLock))

  const storedLock = parseLockRecord(storage.getItem(lockKey))
  return storedLock?.ownerId === ownerId ? nextLock : null
}

function releaseRefreshLock(storage: Storage, lockKey: string, ownerId: string): void {
  const currentLock = parseLockRecord(storage.getItem(lockKey))
  if (currentLock?.ownerId === ownerId) storage.removeItem(lockKey)
}

function publishRefreshResult(storage: Storage, resultKey: string, ownerId: string, ok: boolean): void {
  const result: RefreshResultRecord = {
    ownerId,
    ok,
    completedAt: Date.now(),
  }

  storage.setItem(resultKey, JSON.stringify(result))

  // Best-effort cleanup so localStorage doesn't accumulate stale records.
  // Wait long enough for any waiting tabs to read the value via storage event
  // or the polling loop, then remove it. Failures are ignored.
  if (typeof window !== 'undefined') {
    window.setTimeout(() => {
      try {
        const current = parseResultRecord(storage.getItem(resultKey))
        if (current && current.ownerId === ownerId) storage.removeItem(resultKey)
      } catch {
        // ignore — non-fatal cleanup
      }
    }, WAIT_TIMEOUT_MS)
  }
}

function waitForRefreshResult(storage: Storage, resultKey: string, since: number): Promise<boolean | null> {
  if (typeof window === 'undefined') return Promise.resolve(null)

  return new Promise((resolve) => {
    let finished = false

    const finish = (value: boolean | null) => {
      if (finished) return
      finished = true
      cleanup()
      resolve(value)
    }

    const readResult = () => {
      const result = parseResultRecord(storage.getItem(resultKey))
      if (result && result.completedAt >= since) finish(result.ok)
    }

    function handleStorageEvent(event: StorageEvent) {
      if (event.key === resultKey) readResult()
    }

    window.addEventListener('storage', handleStorageEvent)
    const pollTimer = window.setInterval(readResult, POLL_INTERVAL_MS)
    const timeoutTimer = window.setTimeout(() => finish(null), WAIT_TIMEOUT_MS)

    function cleanup() {
      window.clearInterval(pollTimer)
      window.clearTimeout(timeoutTimer)
      window.removeEventListener('storage', handleStorageEvent)
    }

    readResult()
  })
}

function hasWebLocksApi(): boolean {
  return (
    typeof navigator !== 'undefined'
    && typeof (navigator as Navigator & { locks?: LockManager }).locks?.request === 'function'
  )
}

async function refreshWithWebLock(baseUrl: string, key: string): Promise<boolean> {
  const locks = (navigator as Navigator & { locks: LockManager }).locks
  return locks.request(`${WEB_LOCK_PREFIX}:${key}`, async () => doRefresh(baseUrl))
}

async function refreshWithStorageLock(baseUrl: string, key: string): Promise<boolean> {
  const storage = getRefreshStorage()
  if (!storage) return doRefresh(baseUrl)

  const lockKey = storageKey(LOCK_KEY_PREFIX, key)
  const resultKey = storageKey(RESULT_KEY_PREFIX, key)
  const ownerId = createOwnerId()

  for (let attempt = 0; attempt < 2; attempt += 1) {
    const acquiredLock = tryAcquireRefreshLock(storage, lockKey, ownerId)
    if (acquiredLock) {
      try {
        const ok = await doRefresh(baseUrl)
        publishRefreshResult(storage, resultKey, ownerId, ok)
        return ok
      } finally {
        releaseRefreshLock(storage, lockKey, ownerId)
      }
    }

    const activeLock = parseLockRecord(storage.getItem(lockKey))
    const observedResult = await waitForRefreshResult(storage, resultKey, activeLock?.createdAt ?? Date.now())
    if (observedResult !== null) return observedResult
  }

  return doRefresh(baseUrl)
}

async function refreshWithBrowserLock(baseUrl: string, key: string): Promise<boolean> {
  // Web Locks API is the right primitive for cross-tab coordination —
  // it's atomic and the runtime releases the lock if a tab crashes.
  // localStorage-based locking is kept as a fallback for environments
  // that don't expose `navigator.locks` (older browsers, web workers).
  if (hasWebLocksApi()) return refreshWithWebLock(baseUrl, key)
  return refreshWithStorageLock(baseUrl, key)
}

export function refreshAuthSession(baseUrl: string): Promise<boolean> {
  const key = authBaseKey(baseUrl)
  const existing = refreshPromises.get(key)
  if (existing) return existing

  const promise = refreshWithBrowserLock(baseUrl, key).finally(() => {
    refreshPromises.delete(key)
  })
  refreshPromises.set(key, promise)
  return promise
}
