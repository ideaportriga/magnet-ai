import { fetchData } from '@shared'

interface PromptQueueStep {
  prompt_template_ids: string[]
}

interface PromptQueueConfigData {
  steps?: PromptQueueStep[]
}

interface PromptQueueConfigRecord {
  id: string
  name: string
  system_name: string
  description?: string
  config?: PromptQueueConfigData
  created_at?: string
  updated_at?: string
}

interface State {
  promptQueueConfigs: PromptQueueConfigRecord[]
  selectedPromptQueueConfig: PromptQueueConfigRecord | null
  promptQueueLoading: boolean
}

const state = (): State => ({
  promptQueueConfigs: [],
  selectedPromptQueueConfig: null,
  promptQueueLoading: false,
})

const getters = {
  promptQueueConfigs: (state: State) => state.promptQueueConfigs,
  selectedPromptQueueConfig: (state: State) => state.selectedPromptQueueConfig,
  promptQueueLoading: (state: State) => state.promptQueueLoading,
}

const mutations = {
  setPromptQueueConfigs(state: State, configs: PromptQueueConfigRecord[]) {
    state.promptQueueConfigs = configs
  },
  setSelectedPromptQueueConfig(state: State, config: PromptQueueConfigRecord | null) {
    state.selectedPromptQueueConfig = config
  },
  setPromptQueueLoading(state: State, loading: boolean) {
    state.promptQueueLoading = loading
  },
  addPromptQueueConfig(state: State, config: PromptQueueConfigRecord) {
    state.promptQueueConfigs.push(config)
  },
  removePromptQueueConfig(state: State, configId: string) {
    state.promptQueueConfigs = state.promptQueueConfigs.filter((c) => c.id !== configId)
  },
  updatePromptQueueConfig(state: State, config: PromptQueueConfigRecord) {
    const index = state.promptQueueConfigs.findIndex((c) => c.id === config.id)
    if (index !== -1) {
      state.promptQueueConfigs.splice(index, 1, config)
    }
  },
}

const actions = {
  async fetchPromptQueueConfigs({ commit, state, rootGetters }: any, forceRefresh = false) {
    if (state.promptQueueConfigs?.length > 0 && forceRefresh !== true) {
      return
    }

    commit('setPromptQueueLoading', true)
    try {
      const response = await fetchData({
        method: 'GET',
        endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
        service: 'prompt-queue/configs?limit=1000',
        credentials: 'include',
      })

      if (response?.error) {
        console.error('Failed to fetch prompt queue configs:', response.error)
        commit('setPromptQueueConfigs', [])
        return
      }

      const data = await response.json()
      const configsArray = Array.isArray(data)
        ? data
        : data?.items || data?.data || data?.configs || []

      commit('setPromptQueueConfigs', configsArray)
    } catch (error) {
      console.error('Error fetching prompt queue configs:', error)
      commit('setPromptQueueConfigs', [])
    } finally {
      commit('setPromptQueueLoading', false)
    }
  },

  async createPromptQueueConfig(
    { commit, rootGetters }: any,
    { name, system_name, description, config }: {
      name: string
      system_name: string
      description?: string
      config?: PromptQueueConfigData
    }
  ) {
    commit('setPromptQueueLoading', true)
    try {
      const response = await fetchData({
        method: 'POST',
        endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
        service: 'prompt-queue/configs',
        credentials: 'include',
        body: JSON.stringify({ name, system_name, description, config: config || { steps: [] } }),
        headers: { 'Content-Type': 'application/json' },
      })

      if (response?.error) {
        throw new Error(response.error)
      }

      const data = await response.json()
      commit('addPromptQueueConfig', data)
      return data
    } finally {
      commit('setPromptQueueLoading', false)
    }
  },

  async createPromptQueueConfigFromForm(
    { dispatch }: any,
    payload: { name: string; system_name: string; description?: string; config?: PromptQueueConfigData }
  ) {
    return dispatch('createPromptQueueConfig', payload)
  },

  async fetchPromptQueueConfigById({ commit, rootGetters }: any, configId: string) {
    commit('setPromptQueueLoading', true)
    try {
      const response = await fetchData({
        method: 'GET',
        endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
        service: `prompt-queue/configs/${configId}`,
        credentials: 'include',
      })

      if (response?.error) {
        throw new Error(response.error)
      }

      const data = await response.json()
      commit('setSelectedPromptQueueConfig', data)
      return data
    } finally {
      commit('setPromptQueueLoading', false)
    }
  },

  async updatePromptQueueConfig(
    { commit, rootGetters }: any,
    { configId, updates }: {
      configId: string
      updates: { name?: string; description?: string; system_name?: string; config?: PromptQueueConfigData }
    }
  ) {
    commit('setPromptQueueLoading', true)
    try {
      const response = await fetchData({
        method: 'PATCH',
        endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
        service: `prompt-queue/configs/${configId}`,
        credentials: 'include',
        body: JSON.stringify(updates),
        headers: { 'Content-Type': 'application/json' },
      })

      if (response?.error) {
        throw new Error(response.error)
      }

      const data = await response.json()
      commit('updatePromptQueueConfig', data)
      commit('setSelectedPromptQueueConfig', data)
      return data
    } finally {
      commit('setPromptQueueLoading', false)
    }
  },

  async executePromptQueue(
    { rootGetters }: any,
    { configId, input }: { configId: string; input: Record<string, string> }
  ) {
    const response = await fetchData({
      method: 'POST',
      endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
      service: `prompt-queue/configs/${configId}/execute`,
      credentials: 'include',
      body: JSON.stringify({ input: input || {} }),
      headers: { 'Content-Type': 'application/json' },
    })

    if (response?.error) {
      throw new Error(response.error)
    }

    const data = await response.json()
    return data?.result ?? data
  },

  async deletePromptQueueConfig({ commit, rootGetters }: any, configId: string) {
    commit('setPromptQueueLoading', true)
    try {
      const response = await fetchData({
        method: 'DELETE',
        endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
        service: `prompt-queue/configs/${configId}`,
        credentials: 'include',
      })

      if (response?.error) {
        throw new Error(response.error)
      }

      commit('removePromptQueueConfig', configId)
      commit('setSelectedPromptQueueConfig', null)
    } finally {
      commit('setPromptQueueLoading', false)
    }
  },
}

export default {
  state,
  getters,
  mutations,
  actions,
}
