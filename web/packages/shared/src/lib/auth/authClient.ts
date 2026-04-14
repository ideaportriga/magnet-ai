/**
 * Backward-compatible auth client export.
 *
 * Internally delegates to the unified v2 client (/api/v2/auth/*).
 */

import { createAuthClientV2, type AuthClientV2 } from './authClientV2'

export type AuthClient = AuthClientV2

export function createAuthClient(baseUrl: string): AuthClient {
  return createAuthClientV2(baseUrl)
}
