/**
 * Fetch wrapper with automatic token refresh on 401.
 *
 * Usage:
 *   const authFetch = createAuthFetch(baseUrl, () => router.push('/login'))
 *   const response = await authFetch('/api/some-endpoint', { method: 'GET' })
 */

import { refreshAuthSession } from './refreshCoordinator'

export function createAuthFetch(
  baseUrl: string,
  onUnauthorized: () => void,
) {
  return async function authFetch(
    input: string | URL | Request,
    init?: RequestInit,
  ): Promise<Response> {
    const opts: RequestInit = { credentials: 'include', ...init }
    let response = await fetch(input, opts)

    if (response.status === 401) {
      const refreshed = await refreshAuthSession(baseUrl)

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
