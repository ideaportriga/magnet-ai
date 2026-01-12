import { fetchData } from '@shared'

interface PromptSetting {
  enabled: boolean
  prompt_template: string
}

interface SalesforceIntegrationSettings {
  send_transcript_to_salesforce: boolean
  salesforce_api_server: string
  salesforce_stt_recording_tool: string
}

interface NoteTakerSettings {
  subscription_recordings_ready: boolean
  create_knowledge_graph_embedding: boolean
  knowledge_graph_system_name: string
  integration: {
    salesforce: SalesforceIntegrationSettings
  }
  chapters: PromptSetting
  summary: PromptSetting
  insights: PromptSetting
}

interface State {
  settings: NoteTakerSettings
  loading: boolean
}

const defaultSettings = (): NoteTakerSettings => ({
  subscription_recordings_ready: false,
  create_knowledge_graph_embedding: false,
  knowledge_graph_system_name: '',
  integration: {
    salesforce: {
      send_transcript_to_salesforce: false,
      salesforce_api_server: '',
      salesforce_stt_recording_tool: '',
    },
  },
  chapters: {
    enabled: false,
    prompt_template: '',
  },
  summary: {
    enabled: false,
    prompt_template: '',
  },
  insights: {
    enabled: false,
    prompt_template: '',
  },
})

const mergeSettings = (settings?: Partial<NoteTakerSettings> | null): NoteTakerSettings => ({
  ...defaultSettings(),
  ...(settings || {}),
  integration: {
    ...defaultSettings().integration,
    ...(settings?.integration || {}),
    salesforce: {
      ...defaultSettings().integration.salesforce,
      ...(settings?.integration?.salesforce || {}),
    },
  },
  chapters: {
    ...defaultSettings().chapters,
    ...(settings?.chapters || {}),
  },
  summary: {
    ...defaultSettings().summary,
    ...(settings?.summary || {}),
  },
  insights: {
    ...defaultSettings().insights,
    ...(settings?.insights || {}),
  },
})

// state
const state = (): State => ({
  settings: defaultSettings(),
  loading: false,
})

// getters
const getters = {
  noteTakerSettings: (state: State) => state.settings,
  noteTakerLoading: (state: State) => state.loading,
}

// mutations
const mutations = {
  setNoteTakerSettings(state: State, settings: NoteTakerSettings) {
    state.settings = mergeSettings(settings)
  },
  setNoteTakerLoading(state: State, loading: boolean) {
    state.loading = loading
  },
  updateNoteTakerSetting(state: State, { path, value }: { path: string; value: any }) {
    const keys = path.split('.')
    let target: any = state.settings

    for (let i = 0; i < keys.length - 1; i++) {
      if (!(keys[i] in target) || target[keys[i]] === null) {
        target[keys[i]] = {}
      }
      target = target[keys[i]]
    }

    target[keys[keys.length - 1]] = value
  },
}

// actions
const actions = {
  async fetchNoteTakerSettings({ commit, rootGetters }: any) {
    commit('setNoteTakerLoading', true)
    try {
      const response = await fetchData({
        method: 'GET',
        endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
        service: 'note-taker/settings',
        credentials: 'include',
        headers: {
          Accept: 'application/json',
        },
      })

      if (response?.error || !response?.ok) {
        console.error('Failed to fetch note taker settings:', response?.error)
        return
      }

      const data = await response.json()
      const payload = data?.config ?? data ?? {}
      const normalized = typeof payload === 'string' ? JSON.parse(payload) : payload
      commit('setNoteTakerSettings', normalized || {})
    } catch (error) {
      console.error('Error fetching note taker settings:', error)
    } finally {
      commit('setNoteTakerLoading', false)
    }
  },

  async saveNoteTakerSettings({ state, commit, rootGetters }: any) {
    commit('setNoteTakerLoading', true)
    try {
      const response = await fetchData({
        method: 'PUT',
        endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
        service: 'note-taker/settings',
        credentials: 'include',
        body: JSON.stringify(state.settings),
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
        },
      })

      if (response?.error || !response?.ok) {
        console.error('Failed to save note taker settings:', response?.error)
        throw new Error(response?.error || 'Failed to save note taker settings')
      }
    } finally {
      commit('setNoteTakerLoading', false)
    }
  },

  updateNoteTakerSetting({ commit }: any, payload: { path: string; value: any }) {
    commit('updateNoteTakerSetting', payload)
  },
}

export default {
  state: state(),
  getters,
  mutations,
  actions,
}
