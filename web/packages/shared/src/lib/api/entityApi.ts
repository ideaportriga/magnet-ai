import type { ApiClient } from './apiClient'

export interface PaginationParams {
  currentPage?: number
  pageSize?: number
  orderBy?: string
  sortOrder?: 'asc' | 'desc'
}

export interface ListResponse<T> {
  items: T[]
  total?: number
}

export interface EntityApi<T> {
  list(params?: PaginationParams & Record<string, unknown>): Promise<ListResponse<T>>
  getById(id: string): Promise<T>
  create(data: Partial<T>): Promise<T>
  update(id: string, data: Partial<T>): Promise<T>
  remove(id: string): Promise<void>
  sync(id: string): Promise<unknown>
  test(id: string, body?: unknown): Promise<unknown>
  capabilities(id: string): Promise<unknown>
  debugInfo(id: string): Promise<unknown>
  availableModels(id: string): Promise<unknown>
  custom<R = unknown>(method: 'GET' | 'POST' | 'PATCH' | 'DELETE', subpath: string, body?: unknown): Promise<R>
}

export function createEntityApi<T>(client: ApiClient, servicePath: string): EntityApi<T> {
  function buildPaginationParams(params?: PaginationParams & Record<string, unknown>): Record<string, string | number | boolean | string[]> {
    if (!params) return {}
    const result: Record<string, string | number | boolean | string[]> = {}
    if (params.currentPage !== undefined) result.currentPage = params.currentPage
    if (params.pageSize !== undefined) result.pageSize = params.pageSize
    if (params.orderBy !== undefined) result.orderBy = params.orderBy
    if (params.sortOrder !== undefined) result.sortOrder = params.sortOrder
    // Pass through any extra filter params
    for (const [key, value] of Object.entries(params)) {
      if (['currentPage', 'pageSize', 'orderBy', 'sortOrder'].includes(key)) continue
      if (value !== undefined && value !== null) {
        result[key] = value as string | number | boolean | string[]
      }
    }
    return result
  }

  return {
    async list(params) {
      const queryParams = buildPaginationParams(params)
      const response = await client.get<{ items: T[]; total?: number } | T[]>(servicePath, queryParams)
      // API may return { items: [...], total: N } or just an array
      if (Array.isArray(response)) {
        return { items: response }
      }
      return { items: response.items ?? [], total: response.total }
    },

    async getById(id) {
      return client.get<T>(`${servicePath}/${encodeURIComponent(id)}`)
    },

    async create(data) {
      return client.post<T>(servicePath, data)
    },

    async update(id, data) {
      return client.patch<T>(`${servicePath}/${encodeURIComponent(id)}`, data)
    },

    async remove(id) {
      return client.delete(`${servicePath}/${encodeURIComponent(id)}`)
    },

    async sync(id) {
      return client.post(`${servicePath}/${encodeURIComponent(id)}/sync`)
    },

    async test(id, body) {
      return client.post(`${servicePath}/${encodeURIComponent(id)}/test`, body)
    },

    async capabilities(id) {
      return client.get(`${servicePath}/${encodeURIComponent(id)}/capabilities`)
    },

    async debugInfo(id) {
      return client.get(`${servicePath}/${encodeURIComponent(id)}/debug-info`)
    },

    async availableModels(id) {
      return client.get(`${servicePath}/${encodeURIComponent(id)}/available-models`)
    },

    async custom<R = unknown>(method: 'GET' | 'POST' | 'PATCH' | 'DELETE', subpath: string, body?: unknown): Promise<R> {
      switch (method) {
        case 'GET': return client.get<R>(`${servicePath}/${subpath}`)
        case 'POST': return client.post<R>(`${servicePath}/${subpath}`, body)
        case 'PATCH': return client.patch<R>(`${servicePath}/${subpath}`, body)
        case 'DELETE': {
          await client.delete(`${servicePath}/${subpath}`)
          return undefined as R
        }
      }
    },
  }
}
