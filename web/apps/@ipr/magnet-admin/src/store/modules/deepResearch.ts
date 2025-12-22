import { fetchData } from '@shared'

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
  if (!run) {
    return null
  }

  const id = run?.id ?? run?.run_id
  if (!id) {
    return null
  }

  return {
    ...run,
    id,
    config_id: run?.config_id ?? run?.config?.id ?? null,
    config_system_name: run?.config_system_name ?? run?.config?.system_name ?? null,
  }
}

interface State {
  configs: DeepResearchConfigWithMeta[]
  runs: DeepResearchRun[]
  selectedConfig: DeepResearchConfigWithMeta | null
  selectedRun: DeepResearchRun | null
  loading: boolean
}

// state
const state = (): State => ({
  configs: [],
  runs: [],
  selectedConfig: null,
  selectedRun: null,
  loading: false,
})

// getters
const getters = {
  configs: (state: State) => state.configs,
  runs: (state: State) => state.runs,
  selectedConfig: (state: State) => state.selectedConfig,
  selectedRun: (state: State) => state.selectedRun,
  loading: (state: State) => state.loading,
}

// mutations
const mutations = {
  setConfigs(state: State, configs: DeepResearchConfigWithMeta[]) {
    state.configs = configs
  },
  setRuns(state: State, runs: DeepResearchRun[]) {
    state.runs = runs
  },
  setSelectedConfig(state: State, config: DeepResearchConfigWithMeta | null) {
    state.selectedConfig = config
  },
  setSelectedRun(state: State, run: DeepResearchRun | null) {
    state.selectedRun = run
  },
  setLoading(state: State, loading: boolean) {
    state.loading = loading
  },
  addConfig(state: State, config: DeepResearchConfigWithMeta) {
    state.configs.push(config)
  },
  removeConfig(state: State, configId: string) {
    state.configs = state.configs.filter((c) => c.id !== configId)
  },
  addRun(state: State, run: DeepResearchRun) {
    state.runs.unshift(run) // Add to beginning for most recent first
  },
  updateRun(state: State, run: DeepResearchRun) {
    const index = state.runs.findIndex((r) => r.id === run.id)
    if (index !== -1) {
      state.runs.splice(index, 1, run)
    }
  },
}

// actions
const actions = {
  async fetchConfigs({ commit, state, rootGetters }: any, forceRefresh = false) {
    // If data already exists and not forcing refresh, skip fetch
    if (state.configs?.length > 0 && forceRefresh !== true) {
      return
    }

    commit('setLoading', true)
    try {
      // Fetch all configs without pagination
      const response = await fetchData({
        method: 'GET',
        endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
        service: 'deep-research/configs?limit=1000',
        credentials: rootGetters.config?.credentials,
      })

      if (response?.error) {
        console.error('Failed to fetch configs:', response.error)
        commit('setConfigs', [])
        return
      }

      const data = await response.json()
      const configsArray = Array.isArray(data) ? data : (data?.items || data?.data || data?.configs || [])

      commit('setConfigs', configsArray)
    } catch (error) {
      console.error('Error fetching configs:', error)
      commit('setConfigs', [])
    } finally {
      commit('setLoading', false)
    }
  },

  async createConfig({ commit, dispatch, rootGetters }: any, { name, system_name, config }: { name: string; system_name: string; config: DeepResearchConfig }) {
    commit('setLoading', true)
    try {
      const response = await fetchData({
        method: 'POST',
        endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
        service: 'deep-research/configs',
        credentials: rootGetters.config?.credentials,
        body: JSON.stringify({ name, system_name, config }),
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (response?.error) {
        console.error('Failed to create config:', response.error)
        throw new Error(response.error)
      }

      const data = await response.json()

      // Add the new config to the store immediately
      commit('addConfig', data)

      return data
    } catch (error) {
      console.error('Error creating config:', error)
      throw error
    } finally {
      commit('setLoading', false)
    }
  },

  async deleteConfig({ commit, dispatch, rootGetters }: any, configId: string) {
    commit('setLoading', true)
    try {
      const response = await fetchData({
        method: 'DELETE',
        endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
        service: `deep-research/configs/${configId}`,
        credentials: rootGetters.config?.credentials,
      })

      if (response?.error) {
        console.error('Failed to delete config:', response.error)
        throw new Error(response.error)
      }

      commit('removeConfig', configId)
    } catch (error) {
      console.error('Error deleting config:', error)
      throw error
    } finally {
      commit('setLoading', false)
    }
  },

  async updateConfig({ commit, dispatch, rootGetters }: any, { configId, updates }: { configId: string; updates: { name?: string; description?: string; system_name?: string; config?: DeepResearchConfig } }) {
    commit('setLoading', true)
    try {
      const response = await fetchData({
        method: 'PATCH',
        endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
        service: `deep-research/configs/${configId}`,
        credentials: rootGetters.config?.credentials,
        body: JSON.stringify(updates),
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (response?.error) {
        console.error('Failed to update config:', response.error)
        throw new Error(response.error)
      }

      // Fetch updated list
      await dispatch('fetchConfigs')
    } catch (error) {
      console.error('Error updating config:', error)
      throw error
    } finally {
      commit('setLoading', false)
    }
  },

  async fetchRuns({ commit, rootGetters }: any, payload?: { page?: number; pageSize?: number; orderBy?: string; sortOrder?: string }) {
    commit('setLoading', true)
    try {
      // Build query parameters for pagination
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
        endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
        service: `deep-research/runs?${queryParams.toString()}`,
        credentials: rootGetters.config?.credentials,
      })

      if (response?.error) {
        console.error('Failed to fetch runs:', response.error)
        commit('setRuns', [])
        return { items: [], total: 0 }
      }

      const data = await response.json()
      const runsArray = Array.isArray(data) ? data : (data?.items || data?.data || data?.runs || [])
      const total = data?.total || runsArray.length

      const normalizedRuns = runsArray
        .map((run: any) => normalizeRun(run))
        .filter((run: DeepResearchRun | null): run is DeepResearchRun => Boolean(run))

      commit('setRuns', normalizedRuns)
      return { items: normalizedRuns, total }
    } catch (error) {
      console.error('Error fetching runs:', error)
      commit('setRuns', [])
      return { items: [], total: 0 }
    } finally {
      commit('setLoading', false)
    }
  },

  async createRun(
    { commit, dispatch, rootGetters }: any,
    {
      config,
      input,
      client_id,
      config_system_name,
    }: { config?: DeepResearchConfig; input: Record<string, any>; client_id?: string; config_system_name?: string }
  ) {
    commit('setLoading', true)
    try {
      const response = await fetchData({
        method: 'POST',
        endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
        service: 'deep-research/runs',
        credentials: rootGetters.config?.credentials,
        body: JSON.stringify({ config, input, client_id, config_system_name }),
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (response?.error) {
        console.error('Failed to create run:', response.error)
        throw new Error(response.error)
      }

      const data = await response.json()

      // Fetch updated list
      await dispatch('fetchRuns')

      return normalizeRun(data) ?? data
    } catch (error) {
      console.error('Error creating run:', error)
      throw error
    } finally {
      commit('setLoading', false)
    }
  },

  async createRunFromConfig({ commit, dispatch, rootGetters }: any, { configId, input, client_id }: { configId: string; input: Record<string, any>; client_id?: string }) {
    commit('setLoading', true)
    try {
      const response = await fetchData({
        method: 'POST',
        endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
        service: `deep-research/configs/${configId}/run`,
        credentials: rootGetters.config?.credentials,
        body: JSON.stringify({ input, client_id }),
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (response?.error) {
        console.error('Failed to create run from config:', response.error)
        throw new Error(response.error)
      }

      const data = await response.json()

      // Fetch updated list
      await dispatch('fetchRuns')

      return normalizeRun(data) ?? data
    } catch (error) {
      console.error('Error creating run from config:', error)
      throw error
    } finally {
      commit('setLoading', false)
    }
  },

  async fetchRun({ commit, rootGetters }: any, runId: string) {
    commit('setLoading', true)
    try {
      const response = await fetchData({
        method: 'GET',
        endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
        service: `deep-research/runs/${runId}`,
        credentials: rootGetters.config?.credentials,
      })

      if (response?.error) {
        console.error('Failed to fetch run:', response.error)
        return null
      }

      const run = await response.json()
      const normalizedRun = normalizeRun(run)
      if (normalizedRun) {
        commit('setSelectedRun', normalizedRun)
      }
      return normalizedRun
    } catch (error) {
      console.error('Error fetching run:', error)
      return null
    } finally {
      commit('setLoading', false)
    }
  },
}

export default {
  state,
  getters,
  mutations,
  actions,
}
