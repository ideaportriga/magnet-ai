import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchData } from '@shared'
import { useAppStore } from './appStore'

interface WebhookConfig {
  enabled: boolean
  api_server: string
  api_tool: string
  payload_template?: Record<string, any> | null
}

interface DeepResearchConfig {
  reasoning_prompt: string
  analyze_search_results_prompt: string
  process_search_result_prompt: string
  max_iterations: number
  max_results: number
  parallel_tool_calls?: boolean
  webhook?: WebhookConfig | null
}

interface WebhookCallDetails {
  timestamp: string
  api_server: string
  api_tool: string
  request_payload?: Record<string, any> | null
  response_status?: number | null
  response_body?: Record<string, any> | null
  success: boolean
  error_message?: string | null
}

interface DeepResearchConfigWithMeta {
  id: string
  system_name: string
  name: string
  config: DeepResearchConfig
}

interface DeepResearchRun {
  id: string
  config_id?: string | null
  config_system_name?: string | null
  config?: DeepResearchConfig | null
  client_id?: string | null
  status: 'pending' | 'running' | 'completed' | 'failed' | string
  input: Record<string, any> | null
  memory?: any
  steps?: any[]
  result?: Record<string, any> | null
  error?: string | null
  webhook_call?: WebhookCallDetails | null
  created_at: string
  updated_at: string
  details?: Record<string, any> | null
  total_usage?: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  } | null
  total_latency?: number | null
  total_cost?: number | null
}

const normalizeRun = (run: any): DeepResearchRun | null => {
  if (!run) return null
  const id = run?.id ?? run?.run_id
  if (!id) return null
  return {
    ...run,
    id,
    config_id: run?.config_id ?? run?.config?.id ?? null,
    config_system_name: run?.config_system_name ?? run?.config?.system_name ?? null,
  }
}

export const useDeepResearchStore = defineStore('deepResearch', () => {
  const appStore = useAppStore()

  const configs = ref<DeepResearchConfigWithMeta[]>([])
  const runs = ref<DeepResearchRun[]>([])
  const selectedConfig = ref<DeepResearchConfigWithMeta | null>(null)
  const selectedRun = ref<DeepResearchRun | null>(null)
  const loading = ref(false)

  async function fetchConfigs(forceRefresh = false) {
    if (configs.value.length > 0 && forceRefresh !== true) return

    loading.value = true
    try {
      const response = await fetchData({
        method: 'GET',
        endpoint: appStore.config?.api?.aiBridge?.urlAdmin,
        service: 'deep-research/configs?limit=1000',
        credentials: 'include',
      })

      if (response?.error) {
        configs.value = []
        return
      }

      const data = await response.json()
      const configsArray = Array.isArray(data) ? data : (data?.items || data?.data || data?.configs || [])
      configs.value = configsArray
    } catch (error) {
      configs.value = []
    } finally {
      loading.value = false
    }
  }

  async function createConfig({ name, system_name, config }: { name: string; system_name: string; config: DeepResearchConfig }) {
    loading.value = true
    try {
      const response = await fetchData({
        method: 'POST',
        endpoint: appStore.config?.api?.aiBridge?.urlAdmin,
        service: 'deep-research/configs',
        credentials: 'include',
        body: JSON.stringify({ name, system_name, config }),
        headers: { 'Content-Type': 'application/json' },
      })

      if (response?.error) {
        throw new Error(response.error)
      }

      const data = await response.json()
      configs.value.push(data)
      return data
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function deleteConfig(configId: string) {
    loading.value = true
    try {
      const response = await fetchData({
        method: 'DELETE',
        endpoint: appStore.config?.api?.aiBridge?.urlAdmin,
        service: `deep-research/configs/${configId}`,
        credentials: 'include',
      })

      if (response?.error) {
        throw new Error(response.error)
      }

      configs.value = configs.value.filter((c) => c.id !== configId)
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function updateConfig({ configId, updates }: { configId: string; updates: { name?: string; description?: string; system_name?: string; config?: DeepResearchConfig } }) {
    loading.value = true
    try {
      const response = await fetchData({
        method: 'PATCH',
        endpoint: appStore.config?.api?.aiBridge?.urlAdmin,
        service: `deep-research/configs/${configId}`,
        credentials: 'include',
        body: JSON.stringify(updates),
        headers: { 'Content-Type': 'application/json' },
      })

      if (response?.error) {
        throw new Error(response.error)
      }

      // Fetch updated list
      await fetchConfigs()
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function fetchRuns(payload?: { page?: number; pageSize?: number; orderBy?: string; sortOrder?: string }) {
    loading.value = true
    try {
      const page = payload?.page || 1
      const pageSize = payload?.pageSize || 15
      const orderBy = payload?.orderBy || 'updated_at'
      const sortOrder = payload?.sortOrder || 'desc'

      const queryParams = new URLSearchParams({
        currentPage: page.toString(),
        pageSize: pageSize.toString(),
        orderBy,
        sortOrder,
      })

      const response = await fetchData({
        method: 'GET',
        endpoint: appStore.config?.api?.aiBridge?.urlAdmin,
        service: `deep-research/runs?${queryParams.toString()}`,
        credentials: 'include',
      })

      if (response?.error) {
        runs.value = []
        return { items: [], total: 0 }
      }

      const data = await response.json()
      const runsArray = Array.isArray(data) ? data : (data?.items || data?.data || data?.runs || [])
      const total = data?.total || runsArray.length

      const normalizedRuns = runsArray
        .map((run: any) => normalizeRun(run))
        .filter((run: DeepResearchRun | null): run is DeepResearchRun => Boolean(run))

      runs.value = normalizedRuns
      return { items: normalizedRuns, total }
    } catch (error) {
      runs.value = []
      return { items: [], total: 0 }
    } finally {
      loading.value = false
    }
  }

  async function createRun({
    config,
    input,
    client_id,
    config_system_name,
  }: { config?: DeepResearchConfig; input: Record<string, any>; client_id?: string; config_system_name?: string }) {
    loading.value = true
    try {
      const response = await fetchData({
        method: 'POST',
        endpoint: appStore.config?.api?.aiBridge?.urlAdmin,
        service: 'deep-research/runs',
        credentials: appStore.config?.credentials,
        body: JSON.stringify({ config, input, client_id, config_system_name }),
        headers: { 'Content-Type': 'application/json' },
      })

      if (response?.error) {
        throw new Error(response.error)
      }

      const data = await response.json()

      // Fetch updated list
      await fetchRuns()

      return normalizeRun(data) ?? data
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function createRunFromConfig({ configId, input, client_id }: { configId: string; input: Record<string, any>; client_id?: string }) {
    loading.value = true
    try {
      const response = await fetchData({
        method: 'POST',
        endpoint: appStore.config?.api?.aiBridge?.urlAdmin,
        service: `deep-research/configs/${configId}/run`,
        credentials: appStore.config?.credentials,
        body: JSON.stringify({ input, client_id }),
        headers: { 'Content-Type': 'application/json' },
      })

      if (response?.error) {
        throw new Error(response.error)
      }

      const data = await response.json()

      // Fetch updated list
      await fetchRuns()

      return normalizeRun(data) ?? data
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  async function fetchRun(runId: string) {
    loading.value = true
    try {
      const response = await fetchData({
        method: 'GET',
        endpoint: appStore.config?.api?.aiBridge?.urlAdmin,
        service: `deep-research/runs/${runId}`,
        credentials: appStore.config?.credentials,
      })

      if (response?.error) return null

      const run = await response.json()
      const normalized = normalizeRun(run)
      if (normalized) {
        selectedRun.value = normalized
      }
      return normalized
    } catch (error) {
      return null
    } finally {
      loading.value = false
    }
  }

  return {
    // state
    configs,
    runs,
    selectedConfig,
    selectedRun,
    loading,
    // actions
    fetchConfigs,
    createConfig,
    deleteConfig,
    updateConfig,
    fetchRuns,
    createRun,
    createRunFromConfig,
    fetchRun,
  }
})
