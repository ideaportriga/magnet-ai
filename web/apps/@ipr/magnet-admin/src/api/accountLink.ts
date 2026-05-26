/**
 * Thin client for the `/api/me/account-link/...` endpoints.
 *
 * Uses the shared `apiClient` but with a different baseUrl (urlCommon + '/me')
 * — the default client is wired to `urlAdmin`, which doesn't reach `/api/me`.
 * We build a one-off client lazily on first call.
 */

import { createApiClient, type ApiClient } from '@shared/api'
import { useAppStore } from '@/stores/appStore'

export interface AccountLinkPreview {
  code: string
  provider: string
  channel_kind: string | null
  display_name: string | null
  email: string | null
  extra: Record<string, unknown> | null
  expires_at: string
}

export interface LinkedAccount {
  id: string
  provider: string
  account_id: string
  account_email: string | null
  last_login_at: string | null
  created_at: string | null
}

let _client: ApiClient | null = null

function client(): ApiClient {
  if (_client) return _client
  const appStore = useAppStore()
  const urlCommon = appStore.config?.api.aiBridge.urlCommon
  if (!urlCommon) {
    throw new Error('App config not loaded yet — cannot build /api/me client')
  }
  const credentials = appStore.config?.credentials ?? 'include'
  _client = createApiClient({ baseUrl: `${urlCommon}/me`, credentials })
  return _client
}

export async function previewAccountLinkCode(
  code: string,
): Promise<AccountLinkPreview> {
  return client().get<AccountLinkPreview>(`account-link/${encodeURIComponent(code)}`)
}

export async function confirmAccountLinkCode(code: string): Promise<{ status: string }> {
  return client().post<{ status: string }>(
    `account-link/${encodeURIComponent(code)}/confirm`,
  )
}

export async function listLinkedAccounts(): Promise<LinkedAccount[]> {
  // Note the trailing slash — matches the Litestar route `/`.
  return client().get<LinkedAccount[]>('account-link/')
}

export async function revokeLinkedAccount(linkId: string): Promise<void> {
  await client().delete(`account-link/${encodeURIComponent(linkId)}`)
}
