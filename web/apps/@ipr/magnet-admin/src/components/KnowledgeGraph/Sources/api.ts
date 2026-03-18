import { fetchData } from '@shared'
import type { SourceRow } from './models'

type FetchKnowledgeGraphSourcesOptions = {
  endpoint?: string
  graphId: string
  force?: boolean
}

const pendingSourceRequests = new Map<string, Promise<SourceRow[]>>()
const sourceResponseCache = new Map<string, { rows: SourceRow[]; fetchedAt: number }>()
// Multiple mounted tabs request the same sources payload back-to-back.
const SOURCE_CACHE_WINDOW_MS = 1000

const buildCacheKey = (endpoint: string, graphId: string) => `${endpoint}::${graphId}`

const cloneRows = (rows: SourceRow[]) => JSON.parse(JSON.stringify(rows || [])) as SourceRow[]

export const fetchKnowledgeGraphSources = async ({
  endpoint,
  graphId,
  force = false,
}: FetchKnowledgeGraphSourcesOptions): Promise<SourceRow[]> => {
  if (!endpoint || !graphId) return []

  const cacheKey = buildCacheKey(endpoint, graphId)

  if (force) {
    sourceResponseCache.delete(cacheKey)
  }

  const cached = sourceResponseCache.get(cacheKey)
  if (cached && Date.now() - cached.fetchedAt < SOURCE_CACHE_WINDOW_MS) {
    return cloneRows(cached.rows)
  }

  const pending = pendingSourceRequests.get(cacheKey)
  if (pending) {
    return cloneRows(await pending)
  }

  const request = (async () => {
    const response: any = await fetchData({
      endpoint,
      service: `knowledge_graphs/${graphId}/sources`,
      method: 'GET',
      credentials: 'include',
    })

    if (response?.error) {
      throw response.error
    }

    if (!response?.ok) {
      return []
    }

    const data = await response.json()
    const rows = Array.isArray(data) ? data : data?.items || data?.data || []

    sourceResponseCache.set(cacheKey, {
      rows,
      fetchedAt: Date.now(),
    })

    return rows as SourceRow[]
  })().finally(() => {
    pendingSourceRequests.delete(cacheKey)
  })

  pendingSourceRequests.set(cacheKey, request)

  return cloneRows(await request)
}
