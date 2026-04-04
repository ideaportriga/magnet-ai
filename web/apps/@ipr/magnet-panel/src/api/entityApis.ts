import { createApiClient, createEntityApi } from '@shared/api'
import type { ApiClient, EntityApi } from '@shared/api'
import type { BaseEntity } from '@shared/queries'

export interface PanelEntityApis {
  agents: EntityApi<BaseEntity>
  collections: EntityApi<BaseEntity>
  model: EntityApi<BaseEntity>
  promptTemplates: EntityApi<BaseEntity>
  rag_tools: EntityApi<BaseEntity>
  retrieval: EntityApi<BaseEntity>
  provider: EntityApi<BaseEntity>
}

const SERVICE_PATHS: Record<keyof PanelEntityApis, string> = {
  agents: 'agents',
  collections: 'sql_collections',
  model: 'models',
  promptTemplates: 'prompt_templates',
  rag_tools: 'rag_tools',
  retrieval: 'retrieval_tools',
  provider: 'providers',
}

let _client: ApiClient | null = null
let _apis: PanelEntityApis | null = null

export function createPanelEntityApis(
  baseUrl: string,
  credentials: RequestCredentials = 'include',
  fetchFn?: typeof fetch,
): PanelEntityApis {
  _client = createApiClient({ baseUrl, credentials, fetchFn })

  _apis = {} as PanelEntityApis
  for (const [key, path] of Object.entries(SERVICE_PATHS)) {
    ;(_apis as Record<string, EntityApi<BaseEntity>>)[key] = createEntityApi(_client, path)
  }

  return _apis
}

export function getPanelEntityApis(): PanelEntityApis {
  if (!_apis) throw new Error('Panel entity APIs not initialized.')
  return _apis
}

export function getPanelApiClient(): ApiClient {
  if (!_client) throw new Error('Panel API client not initialized.')
  return _client
}
