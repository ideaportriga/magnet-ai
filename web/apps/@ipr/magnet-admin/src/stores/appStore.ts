import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export interface ServiceConfig {
  endpoint: string
  credentials: RequestCredentials | null
  service: string
  [key: string]: unknown
}

export interface AppConfig {
  auth: {
    enabled: boolean
    provider?: string
    providers?: string[]
    signupEnabled?: boolean
    [key: string]: unknown
  }
  api: {
    aiBridge: {
      baseUrl: string
      urlCommon: string
      urlAdmin: string
      urlUser: string
    }
    apiRaw?: Record<string, unknown>
  }
  environment?: string
  credentials: RequestCredentials
  panel?: { baseUrl?: string }
  admin?: { baseUrl?: string }
  // Service sub-configs (backward compat with Vuex config shape)
  search?: ServiceConfig
  rag?: ServiceConfig
  model?: ServiceConfig
  retrieval?: ServiceConfig
  agent?: ServiceConfig
  scheduler?: ServiceConfig
  agent_conversations?: ServiceConfig
  collections?: ServiceConfig
  documentSemanticSearch?: ServiceConfig
  chatCompletion?: ServiceConfig & { inputs?: Record<string, unknown> }
  prompts?: ServiceConfig & { headers?: Record<string, string> }
  feedbacks?: ServiceConfig
  mcp_servers?: ServiceConfig
  specifications?: ServiceConfig
  [key: string]: unknown
}

export const useAppStore = defineStore('app', () => {
  const config = ref<AppConfig | null>(null)
  const globalLoading = ref(false)
  const errorMessage = ref<{
    text: string
    technicalError?: string
    stack?: string
    route?: string
    timestamp?: string
    statusCode?: number
    requestUrl?: string
  } | null>(null)

  const adminEndpoint = computed(() => config.value?.api.aiBridge.urlAdmin ?? '')
  const userEndpoint = computed(() => config.value?.api.aiBridge.urlUser ?? '')
  const credentials = computed<RequestCredentials>(() => config.value?.credentials ?? 'include')

  async function loadConfig(): Promise<AppConfig> {
    const publicPath = (window as Record<string, unknown>).__publicPath ?? '/admin/'
    const response = await fetch(`${publicPath}config/main.json`)
    const raw = await response.json()

    const baseUrl = raw.api?.aiBridge?.baseUrl ?? ''
    const authEnabled = raw.auth?.enabled === true || raw.auth?.enabled === 'true'

    const urlCommon = `${baseUrl}/api`
    const urlAdmin = `${urlCommon}/admin`
    const urlUser = `${urlCommon}/user`
    const creds: RequestCredentials | null = authEnabled ? 'include' : null

    const svc = (service: string, endpoint = urlAdmin): ServiceConfig => ({
      endpoint,
      credentials: creds,
      service,
    })

    const parsed: AppConfig = {
      ...raw,
      auth: {
        ...raw.auth,
        enabled: authEnabled,
      },
      api: {
        ...raw.api,
        apiRaw: raw.api,
        aiBridge: {
          baseUrl,
          urlCommon,
          urlAdmin,
          urlUser,
        },
      },
      credentials: authEnabled ? 'include' : 'same-origin',
      environment: raw.environment ?? '',
      panel: { baseUrl: raw.panel?.baseUrl ?? window.location.origin },
      admin: { baseUrl: raw.admin?.baseUrl ?? window.location.origin },
      // Service sub-configs (backward compat with Vuex config shape)
      search: svc('search'),
      rag: svc('rag_tools'),
      model: svc('models'),
      retrieval: svc('retrieval_tools'),
      agent: svc('agents'),
      scheduler: svc('scheduler'),
      agent_conversations: svc('agent_conversations', urlUser),
      collections: { ...svc('collections'), hidden: [], default: 'TODO' },
      documentSemanticSearch: svc('rag/retrieve'),
      chatCompletion: { ...svc('prompt_templates/test'), inputs: { model: 'gpt-35-turbo', temperature: 1, topP: 1 } },
      prompts: { ...svc('prompt_templates'), headers: { 'Content-Type': 'application/json' } },
      feedbacks: svc('feedbacks'),
      mcp_servers: svc('mcp_servers'),
      specifications: svc('specifications'),
    }

    config.value = parsed
    return parsed
  }

  function setErrorMessage(error: { text: string; technicalError?: string; stack?: string; statusCode?: number; requestUrl?: string } | null) {
    if (error) {
      errorMessage.value = {
        ...error,
        timestamp: new Date().toISOString(),
        route: typeof window !== 'undefined' ? window.location.hash || window.location.pathname : '',
      }
    } else {
      errorMessage.value = null
    }
  }

  return {
    config,
    globalLoading,
    errorMessage,
    adminEndpoint,
    userEndpoint,
    credentials,
    loadConfig,
    setErrorMessage,
  }
})
