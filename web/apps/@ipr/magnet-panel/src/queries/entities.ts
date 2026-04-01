import type { PanelEntityApis } from '@/api/entityApis'
import { createEntityQueries, type EntityQueries, type BaseEntity } from '@shared/queries'

export interface PanelEntityQueries {
  agents: EntityQueries<BaseEntity>
  collections: EntityQueries<BaseEntity>
  model: EntityQueries<BaseEntity>
  promptTemplates: EntityQueries<BaseEntity>
  rag_tools: EntityQueries<BaseEntity>
  retrieval: EntityQueries<BaseEntity>
  provider: EntityQueries<BaseEntity>
}

let _queries: PanelEntityQueries | null = null

export function initPanelEntityQueries(apis: PanelEntityApis): PanelEntityQueries {
  _queries = {
    agents: createEntityQueries('agents', apis.agents),
    collections: createEntityQueries('collections', apis.collections),
    model: createEntityQueries('model', apis.model),
    promptTemplates: createEntityQueries('promptTemplates', apis.promptTemplates),
    rag_tools: createEntityQueries('rag_tools', apis.rag_tools),
    retrieval: createEntityQueries('retrieval', apis.retrieval),
    provider: createEntityQueries('provider', apis.provider),
  }
  return _queries
}

export function usePanelEntityQueries(): PanelEntityQueries {
  if (!_queries) throw new Error('Panel entity queries not initialized.')
  return _queries
}
