/**
 * Admin-side client for `/api/admin/account-link/...`.
 *
 * Uses the default admin `apiClient` (baseUrl = urlAdmin), so paths are
 * relative ("account-link/...", not "/api/admin/account-link/...").
 */

import { getApiClient } from './entityApis'

export interface AdminLinkedAccount {
  id: string
  provider: string
  account_id: string
  account_email: string | null
  last_login_at: string | null
  created_at: string | null
}

export async function adminListLinkedAccounts(
  userId?: string,
): Promise<AdminLinkedAccount[]> {
  const client = getApiClient()
  const params = userId ? { user_id: userId } : undefined
  return client.get<AdminLinkedAccount[]>('account-link/', params)
}

export async function adminRevokeLinkedAccount(linkId: string): Promise<void> {
  const client = getApiClient()
  await client.delete(`account-link/${encodeURIComponent(linkId)}`)
}
