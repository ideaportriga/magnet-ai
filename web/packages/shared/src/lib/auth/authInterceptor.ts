/**
 * Fetch wrapper with automatic token refresh on 401.
 *
 * Usage:
 *   const authFetch = createAuthFetch(baseUrl, () => router.push('/login'))
 *   const response = await authFetch('/api/some-endpoint', { method: 'GET' })
 */

export function createAuthFetch(
  baseUrl: string,
  onUnauthorized: () => void,
) {
  let refreshPromise: Promise<boolean> | null = null

  async function doRefresh(): Promise<boolean> {
    try {
      const res = await fetch(`${baseUrl}/api/v2/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
      })
      return res.ok
    } catch {
      return false
    }
  }

  return async function authFetch(
    input: string | URL | Request,
    init?: RequestInit,
  ): Promise<Response> {
    const opts: RequestInit = { credentials: 'include', ...init }
    let response = await fetch(input, opts)

    if (response.status === 401) {
      // Deduplicate concurrent refresh attempts
      if (!refreshPromise) {
        refreshPromise = doRefresh().finally(() => {
          refreshPromise = null
        })
      }

      const refreshed = await refreshPromise

      if (refreshed) {
        // Retry the original request
        response = await fetch(input, opts)
      } else {
        onUnauthorized()
      }
    }

    return response
  }
}
