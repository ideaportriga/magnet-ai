export interface ApiClientConfig {
  baseUrl: string
  credentials?: RequestCredentials
  fetchFn?: typeof fetch
}

export interface ApiError {
  status: number
  statusText: string
  body: string
}

export interface ApiClient {
  get<T>(path: string, params?: Record<string, string | number | boolean | string[]>): Promise<T>
  post<T>(path: string, body?: unknown): Promise<T>
  patch<T>(path: string, body?: unknown): Promise<T>
  delete(path: string): Promise<void>
  postRaw(path: string, body?: unknown, signal?: AbortSignal): Promise<Response>
}

function buildUrl(baseUrl: string, path: string, params?: Record<string, string | number | boolean | string[]>): string {
  const url = `${baseUrl}/${path}`
  if (!params || Object.keys(params).length === 0) return url

  const searchParams = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null) continue
    if (Array.isArray(value)) {
      for (const v of value) searchParams.append(key, v)
    } else {
      searchParams.append(key, String(value))
    }
  }
  const qs = searchParams.toString()
  return qs ? `${url}?${qs}` : url
}

export class ApiRequestError extends Error implements ApiError {
  status: number
  statusText: string
  body: string
  requestUrl: string

  constructor(response: Response, body: string) {
    // Try to extract error message from JSON response body
    let serverMessage = ''
    try {
      const parsed = JSON.parse(body)
      serverMessage = parsed?.error || parsed?.detail || parsed?.message || ''
    } catch {
      // body is not JSON
    }
    const message = serverMessage || `${response.status} ${response.statusText}`
    super(message)
    this.name = 'ApiRequestError'
    this.status = response.status
    this.statusText = response.statusText
    this.body = body
    this.requestUrl = response.url
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.text().catch(() => '')
    throw new ApiRequestError(response, body)
  }
  const text = await response.text()
  return text ? JSON.parse(text) : undefined
}

export function createApiClient(config: ApiClientConfig): ApiClient {
  const { baseUrl, credentials = 'include', fetchFn = fetch } = config

  const jsonHeaders = { 'Content-Type': 'application/json' }

  return {
    async get<T>(path: string, params?: Record<string, string | number | boolean | string[]>): Promise<T> {
      const response = await fetchFn(buildUrl(baseUrl, path, params), {
        method: 'GET',
        credentials,
      })
      return handleResponse<T>(response)
    },

    async post<T>(path: string, body?: unknown): Promise<T> {
      const response = await fetchFn(buildUrl(baseUrl, path), {
        method: 'POST',
        credentials,
        headers: jsonHeaders,
        body: body !== undefined ? JSON.stringify(body) : undefined,
      })
      return handleResponse<T>(response)
    },

    async patch<T>(path: string, body?: unknown): Promise<T> {
      const response = await fetchFn(buildUrl(baseUrl, path), {
        method: 'PATCH',
        credentials,
        headers: jsonHeaders,
        body: body !== undefined ? JSON.stringify(body) : undefined,
      })
      return handleResponse<T>(response)
    },

    async delete(path: string): Promise<void> {
      const response = await fetchFn(buildUrl(baseUrl, path), {
        method: 'DELETE',
        credentials,
        headers: jsonHeaders,
      })
      if (!response.ok) {
        const body = await response.text().catch(() => '')
        throw { status: response.status, statusText: response.statusText, body } as ApiError
      }
    },

    async postRaw(path: string, body?: unknown, signal?: AbortSignal): Promise<Response> {
      return fetchFn(buildUrl(baseUrl, path), {
        method: 'POST',
        credentials,
        headers: jsonHeaders,
        body: body !== undefined ? JSON.stringify(body) : undefined,
        signal,
      })
    },
  }
}
