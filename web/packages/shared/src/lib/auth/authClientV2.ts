/**
 * Unified v2 auth API client — all endpoints under /api/v2/auth/*
 *
 * This client replaces the mixed legacy client that called both
 * /auth/* and /api/auth/* endpoints.
 *
 * SSO login is handled via server-side redirect (no popup).
 */

import type {
  AuthorizationUrlInfo,
  LoginResult,
  MfaSetupInfo,
  SessionInfo,
  SignupResult,
  UserInfo,
} from './types'

export interface ProviderInfo {
  name: string
  type: 'oidc' | 'oauth2'
}

export interface AuthClientV2 {
  me(): Promise<UserInfo | null>
  loginLocal(email: string, password: string): Promise<LoginResult>
  signup(email: string, password: string, name?: string): Promise<SignupResult>
  refresh(): Promise<boolean>
  logout(): Promise<void>
  forgotPassword(email: string): Promise<void>
  resetPassword(token: string, newPassword: string): Promise<void>
  verifyMfa(code: string): Promise<LoginResult>
  getSessions(): Promise<SessionInfo[]>
  revokeSession(id: string): Promise<void>
  revokeAllSessions(): Promise<void>
  getMfaSetup(): Promise<MfaSetupInfo>
  confirmMfaSetup(secret: string, totpCode: string): Promise<{ backup_codes: string[] }>
  disableMfa(password?: string): Promise<void>
  getProviders(): Promise<ProviderInfo[]>
  /** Returns the SSO redirect URL. Navigate to it to start SSO login. */
  getSsoUrl(provider: string): string
  // Legacy compat — delegates to loginLocal or is a no-op
  completeOidc(body: unknown): Promise<boolean>
  getOAuthUrl(provider: string): Promise<AuthorizationUrlInfo>
}

async function jsonOrNull(response: Response) {
  try {
    return await response.json()
  } catch {
    return null
  }
}

export function createAuthClientV2(baseUrl: string): AuthClientV2 {
  const v2 = (path: string) => `${baseUrl}/api/v2/auth${path}`

  const f = (url: string, opts: RequestInit = {}) =>
    fetch(url, {
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', ...opts.headers },
      ...opts,
    })

  return {
    async me() {
      const res = await f(v2('/me'))
      if (!res.ok) return null
      return res.json()
    },

    async loginLocal(email, password) {
      const res = await f(v2('/login'), {
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
      const res = await f(v2('/signup'), {
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
      const res = await f(v2('/refresh'), { method: 'POST' })
      return res.ok
    },

    async logout() {
      await f(v2('/logout'), { method: 'POST' }).catch(() => {
        // silently ignore logout failures
      })
    },

    async forgotPassword(email) {
      await f(v2('/password/forgot'), {
        method: 'POST',
        body: JSON.stringify({ email }),
      })
    },

    async resetPassword(token, newPassword) {
      const res = await f(v2('/password/reset'), {
        method: 'POST',
        body: JSON.stringify({ token, new_password: newPassword }),
      })
      if (!res.ok) {
        const data = await jsonOrNull(res)
        throw new Error(data?.detail || 'Reset failed')
      }
    },

    async verifyMfa(code) {
      const res = await f(v2('/mfa/verify'), {
        method: 'POST',
        body: JSON.stringify({ code }),
      })
      if (!res.ok) {
        const data = await jsonOrNull(res)
        throw new Error(data?.detail || 'MFA verification failed')
      }
      return res.json()
    },

    async getSessions() {
      const res = await f(v2('/sessions'))
      if (!res.ok) return []
      return res.json()
    },

    async revokeSession(id) {
      await f(v2(`/sessions/${id}`), { method: 'DELETE' })
    },

    async revokeAllSessions() {
      await f(v2('/sessions'), { method: 'DELETE' })
    },

    async getMfaSetup() {
      const res = await f(v2('/mfa/setup'))
      if (!res.ok) throw new Error('Failed to get MFA setup')
      return res.json()
    },

    async confirmMfaSetup(secret, totpCode) {
      const res = await f(v2('/mfa/confirm'), {
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
      const res = await f(v2('/mfa'), {
        method: 'DELETE',
        body: JSON.stringify({ password: password || null }),
      })
      if (!res.ok) {
        const data = await jsonOrNull(res)
        throw new Error(data?.detail || 'Failed to disable MFA')
      }
    },

    async getProviders() {
      const res = await f(v2('/providers'))
      if (!res.ok) return []
      return res.json()
    },

    getSsoUrl(provider) {
      // Server-side redirect — just navigate to this URL
      return `${baseUrl}/api/v2/auth/sso/${provider}`
    },

    // Legacy compat — v2 uses server-side redirect, but legacy popup
    // flow calls completeOidc with OIDC tokens. Forward to legacy endpoint.
    async completeOidc(body) {
      const res = await f(`${baseUrl}/auth/complete`, {
        method: 'POST',
        body: JSON.stringify(body),
      })
      return res.ok
    },

    // Legacy compat — return SSO redirect URL for providers
    async getOAuthUrl(provider) {
      return {
        authorization_url: `${baseUrl}/api/v2/auth/sso/${provider}`,
        state: '',
      }
    },
  }
}
