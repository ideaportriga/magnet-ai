/**
 * Framework-agnostic auth API client.
 *
 * Works with both Pinia (magnet-panel) and Vuex (magnet-admin).
 * All methods use fetch with credentials: 'include' for HttpOnly cookie auth.
 */

import type {
  AuthorizationUrlInfo,
  LoginResult,
  MfaSetupInfo,
  SessionInfo,
  SignupResult,
  UserInfo,
} from './types'

export interface AuthClient {
  me(): Promise<UserInfo | null>
  loginLocal(email: string, password: string): Promise<LoginResult>
  signup(email: string, password: string, name?: string): Promise<SignupResult>
  refresh(): Promise<boolean>
  logout(): Promise<void>
  completeOidc(body: unknown): Promise<boolean>
  forgotPassword(email: string): Promise<void>
  resetPassword(token: string, newPassword: string): Promise<void>
  verifyMfa(code: string): Promise<LoginResult>
  getOAuthUrl(provider: string): Promise<AuthorizationUrlInfo>
  getSessions(): Promise<SessionInfo[]>
  revokeSession(id: string): Promise<void>
  revokeAllSessions(): Promise<void>
  getMfaSetup(): Promise<MfaSetupInfo>
  confirmMfaSetup(secret: string, totpCode: string): Promise<{ backup_codes: string[] }>
  disableMfa(password?: string): Promise<void>
}

async function jsonOrNull(response: Response) {
  try {
    return await response.json()
  } catch {
    return null
  }
}

export function createAuthClient(baseUrl: string): AuthClient {
  const apiUrl = (path: string) => `${baseUrl}${path}`

  const f = (url: string, opts: RequestInit = {}) =>
    fetch(url, {
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', ...opts.headers },
      ...opts,
    })

  return {
    async me() {
      const res = await f(apiUrl('/auth/me'))
      if (!res.ok) return null
      return res.json()
    },

    async loginLocal(email, password) {
      const res = await f(apiUrl('/api/auth/login'), {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      })
      if (!res.ok) {
        const data = await jsonOrNull(res)
        throw new Error(data?.detail || 'Login failed')
      }
      return res.json()
    },

    async signup(email, password, name?) {
      const res = await f(apiUrl('/api/auth/signup'), {
        method: 'POST',
        body: JSON.stringify({ email, password, name }),
      })
      if (!res.ok) {
        const data = await jsonOrNull(res)
        throw new Error(data?.detail || 'Signup failed')
      }
      return res.json()
    },

    async refresh() {
      const res = await f(apiUrl('/api/auth/refresh'), { method: 'POST' })
      return res.ok
    },

    async logout() {
      // Local auth logout — revoke refresh token family + clear cookies
      await f(apiUrl('/api/auth/logout'), { method: 'POST' }).catch(() => { /* ignore */ })
      // Also try OIDC logout (clears OIDC cookies)
      await f(apiUrl('/auth/logout'), { method: 'POST' }).catch(() => { /* ignore */ })
    },

    async completeOidc(body) {
      const res = await f(apiUrl('/auth/complete'), {
        method: 'POST',
        body: JSON.stringify(body),
      })
      return res.ok
    },

    async forgotPassword(email) {
      await f(apiUrl('/api/auth/forgot-password'), {
        method: 'POST',
        body: JSON.stringify({ email }),
      })
    },

    async resetPassword(token, newPassword) {
      const res = await f(apiUrl('/api/auth/reset-password'), {
        method: 'POST',
        body: JSON.stringify({ token, new_password: newPassword }),
      })
      if (!res.ok) {
        const data = await jsonOrNull(res)
        throw new Error(data?.detail || 'Reset failed')
      }
    },

    async verifyMfa(code) {
      const res = await f(apiUrl('/api/auth/mfa/verify'), {
        method: 'POST',
        body: JSON.stringify({ code }),
      })
      if (!res.ok) {
        const data = await jsonOrNull(res)
        throw new Error(data?.detail || 'MFA verification failed')
      }
      return res.json()
    },

    async getOAuthUrl(provider) {
      const res = await f(apiUrl(`/api/auth/oauth/${provider}`))
      if (!res.ok) throw new Error('Failed to get OAuth URL')
      return res.json()
    },

    async getSessions() {
      const res = await f(apiUrl('/api/auth/sessions'))
      if (!res.ok) return []
      return res.json()
    },

    async revokeSession(id) {
      await f(apiUrl(`/api/auth/sessions/${id}`), { method: 'DELETE' })
    },

    async revokeAllSessions() {
      await f(apiUrl('/api/auth/sessions'), { method: 'DELETE' })
    },

    async getMfaSetup() {
      const res = await f(apiUrl('/api/auth/mfa/setup'))
      if (!res.ok) throw new Error('Failed to get MFA setup')
      return res.json()
    },

    async confirmMfaSetup(secret, totpCode) {
      const res = await f(apiUrl('/api/auth/mfa/setup/confirm'), {
        method: 'POST',
        body: JSON.stringify({ secret, totp_code: totpCode }),
      })
      if (!res.ok) {
        const data = await jsonOrNull(res)
        throw new Error(data?.detail || 'MFA confirmation failed')
      }
      return res.json()
    },

    async disableMfa(password?) {
      const res = await f(apiUrl('/api/auth/mfa'), {
        method: 'DELETE',
        body: JSON.stringify({ password: password || null }),
      })
      if (!res.ok) {
        const data = await jsonOrNull(res)
        throw new Error(data?.detail || 'Failed to disable MFA')
      }
    },
  }
}
