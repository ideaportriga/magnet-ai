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

interface ConfluenceIntegrationSettings {
  enabled: boolean
  confluence_api_server: string
  confluence_create_page_tool: string
  space_key: string
  parent_id: string
  content_format: 'markdown' | 'wiki' | 'storage'
  enable_heading_anchors: boolean
  title_template: string
  // Backward compatibility (old MCP-based settings)
  mcp_server_system_name?: string
  tool_system_name?: string
}

interface NoteTakerSettings {
  subscription_recordings_ready: boolean
  create_knowledge_graph_embedding: boolean
  knowledge_graph_system_name: string
  integration: {
    confluence: ConfluenceIntegrationSettings
    salesforce: SalesforceIntegrationSettings
  }
  chapters: PromptSetting
  summary: PromptSetting
  insights: PromptSetting
}

interface NoteTakerSettingsRecord {
  key: string
  id?: string
  name?: string
  system_name?: string
  description?: string
  created_at?: string
  updated_at?: string
  config: NoteTakerSettings
}

interface State {
  settings: NoteTakerSettings
  settingsRecords: NoteTakerSettingsRecord[]
  activeSettingsKey: string | null
  loading: boolean
}

const DEFAULT_SETTINGS_KEY = 'default'

const defaultSettings = (): NoteTakerSettings => ({
  subscription_recordings_ready: false,
  create_knowledge_graph_embedding: false,
  knowledge_graph_system_name: '',
  integration: {
    confluence: {
      enabled: false,
      confluence_api_server: '',
      confluence_create_page_tool: '',
      space_key: '',
      parent_id: '',
      content_format: 'markdown',
      enable_heading_anchors: true,
      title_template: 'Meeting notes: {meeting_title} ({date})',
    },
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

const mergeSettings = (settings?: Partial<NoteTakerSettings> | null): NoteTakerSettings => {
  const defaults = defaultSettings()
  const mergedConfluence: ConfluenceIntegrationSettings = {
    ...defaults.integration.confluence,
    ...((settings?.integration as any)?.confluence || {}),
  }

  if (!mergedConfluence.confluence_api_server && mergedConfluence.mcp_server_system_name) {
    mergedConfluence.confluence_api_server = mergedConfluence.mcp_server_system_name
  }
  if (!mergedConfluence.confluence_create_page_tool && mergedConfluence.tool_system_name) {
    mergedConfluence.confluence_create_page_tool = mergedConfluence.tool_system_name
  }

  return {
    ...defaults,
    ...(settings || {}),
    integration: {
      ...defaults.integration,
      ...(settings?.integration || {}),
      confluence: mergedConfluence,
      salesforce: {
        ...defaults.integration.salesforce,
        ...(settings?.integration?.salesforce || {}),
      },
    },
    chapters: {
      ...defaults.chapters,
      ...(settings?.chapters || {}),
    },
    summary: {
      ...defaults.summary,
      ...(settings?.summary || {}),
    },
    insights: {
      ...defaults.insights,
      ...(settings?.insights || {}),
    },
  }
}

const toSettingsConfig = (payload: any): NoteTakerSettings => {
  let normalized = payload
  if (typeof normalized === 'string') {
    try {
      normalized = JSON.parse(normalized)
    } catch (error) {
      normalized = {}
    }
  }
  return mergeSettings(normalized || {})
}

const normalizeSettingsPayload = (payload: any): NoteTakerSettingsRecord[] => {
  const items = Array.isArray(payload)
    ? payload
    : Array.isArray(payload?.items)
      ? payload.items
      : Array.isArray(payload?.data)
        ? payload.data
        : payload
          ? [payload]
          : []

  if (!items.length) {
    return []
  }

  return items.map((item: any, index: number) => {
    const id = item?.id ? String(item.id) : undefined
    const systemName = item?.system_name ? String(item.system_name) : undefined
    const key = id || systemName || `${DEFAULT_SETTINGS_KEY}-${index}`
    const configSource = item?.config ?? item?.settings ?? item

    return {
      key,
      id,
      system_name: systemName,
      name: item?.name,
      description: item?.description,
      created_at: item?.created_at,
      updated_at: item?.updated_at,
      config: toSettingsConfig(configSource),
    }
  })
}

// state
const state = (): State => ({
  settings: defaultSettings(),
  settingsRecords: [],
  activeSettingsKey: null,
  loading: false,
})

// getters
const getters = {
  noteTakerSettings: (state: State) => state.settings,
  noteTakerSettingsRecords: (state: State) => state.settingsRecords,
  noteTakerSettingsActiveKey: (state: State) => state.activeSettingsKey,
  noteTakerSettingsActiveRecord: (state: State) =>
    state.settingsRecords.find((record) => record.key === state.activeSettingsKey) || null,
  noteTakerLoading: (state: State) => state.loading,
}

// mutations
const mutations = {
  setNoteTakerSettings(state: State, settings: NoteTakerSettings) {
    state.settings = mergeSettings(settings)
  },
  setNoteTakerSettingsRecords(state: State, records: NoteTakerSettingsRecord[]) {
    state.settingsRecords = records
  },
  setNoteTakerActiveSettingsKey(state: State, key: string | null) {
    state.activeSettingsKey = key
  },
  setNoteTakerRecordMeta(
    state: State,
    payload: { key: string | null; name?: string; description?: string; system_name?: string }
  ) {
    if (!payload.key) return
    const index = state.settingsRecords.findIndex((record) => record.key === payload.key)
    if (index < 0) return
    state.settingsRecords[index] = {
      ...state.settingsRecords[index],
      name: payload.name ?? state.settingsRecords[index].name,
      description: payload.description ?? state.settingsRecords[index].description,
      system_name: payload.system_name ?? state.settingsRecords[index].system_name,
    }
  },
  setNoteTakerRecordConfig(state: State, payload: { key: string | null; config: NoteTakerSettings }) {
    if (!payload.key) return
    const index = state.settingsRecords.findIndex((record) => record.key === payload.key)
    if (index < 0) return
    state.settingsRecords[index] = {
      ...state.settingsRecords[index],
      config: mergeSettings(payload.config),
    }
  },
  setNoteTakerLoading(state: State, loading: boolean) {
    state.loading = loading
  },
  addNoteTakerRecord(state: State, record: NoteTakerSettingsRecord) {
    state.settingsRecords.push(record)
  },
  upsertNoteTakerRecord(state: State, record: NoteTakerSettingsRecord) {
    const index = state.settingsRecords.findIndex((item) => {
      if (record.id && item.id === record.id) return true
      if (record.system_name && item.system_name === record.system_name) return true
      return item.key === record.key
    })

    if (index >= 0) {
      state.settingsRecords.splice(index, 1, record)
    } else {
      state.settingsRecords.push(record)
    }
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

    const activeKey = state.activeSettingsKey
    if (activeKey) {
      const recordIndex = state.settingsRecords.findIndex((record) => record.key === activeKey)
      if (recordIndex >= 0) {
        state.settingsRecords[recordIndex] = {
          ...state.settingsRecords[recordIndex],
          config: mergeSettings(state.settings),
        }
      }
    }
  },
}

// actions
const actions = {
  async fetchNoteTakerSettings({ commit, state, rootGetters }: any, forceRefresh = false) {
    commit('setNoteTakerLoading', true)
    try {
      if (state.settingsRecords.length > 0 && !forceRefresh) {
        return
      }
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
      const records = normalizeSettingsPayload(data)
      commit('setNoteTakerSettingsRecords', records)

      if (!records.length) {
        commit('setNoteTakerActiveSettingsKey', null)
        commit('setNoteTakerSettings', defaultSettings())
        return
      }

      let activeKey = state.activeSettingsKey
      if (!activeKey || !records.find((record) => record.key === activeKey)) {
        activeKey = records[0]?.key || null
      }

      commit('setNoteTakerActiveSettingsKey', activeKey)

      const activeRecord = records.find((record) => record.key === activeKey)
      commit('setNoteTakerSettings', activeRecord?.config || defaultSettings())
    } catch (error) {
      console.error('Error fetching note taker settings:', error)
    } finally {
      commit('setNoteTakerLoading', false)
    }
  },

  async saveNoteTakerSettings({ state, commit, rootGetters }: any) {
    commit('setNoteTakerLoading', true)
    try {
      const activeRecord = state.settingsRecords.find(
        (record: NoteTakerSettingsRecord) => record.key === state.activeSettingsKey
      )
      const recordId = activeRecord?.id || activeRecord?.system_name
      const service = recordId
        ? `note-taker/settings/${encodeURIComponent(recordId)}`
        : 'note-taker/settings'

      const useRecordPayload = Boolean(
        activeRecord?.id || activeRecord?.system_name || activeRecord?.name || activeRecord?.description
      )
      const payload = useRecordPayload
        ? {
            id: activeRecord?.id,
            name: activeRecord?.name,
            system_name: activeRecord?.system_name,
            description: activeRecord?.description,
            config: state.settings,
          }
        : state.settings

      const response = await fetchData({
        method: 'PUT',
        endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
        service,
        credentials: 'include',
        body: JSON.stringify(payload),
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
        },
      })

      if (response?.error || !response?.ok) {
        console.error('Failed to save note taker settings:', response?.error)
        throw new Error(response?.error || 'Failed to save note taker settings')
      }

      // Prefer server response as the source of truth (keeps name/description/system_name in sync).
      try {
        const data = await response.json()
        const record = normalizeSettingsPayload(data)[0]
        if (record) {
          commit('upsertNoteTakerRecord', record)
          commit('setNoteTakerActiveSettingsKey', record.key)
          commit('setNoteTakerSettings', record.config)
        } else {
          commit('setNoteTakerRecordConfig', {
            key: state.activeSettingsKey,
            config: state.settings,
          })
        }
      } catch {
        commit('setNoteTakerRecordConfig', {
          key: state.activeSettingsKey,
          config: state.settings,
        })
      }
    } finally {
      commit('setNoteTakerLoading', false)
    }
  },

  async createNoteTakerSettings(
    { commit, rootGetters }: any,
    payload: { name: string; system_name: string; description?: string; config?: NoteTakerSettings }
  ) {
    commit('setNoteTakerLoading', true)
    try {
      const response = await fetchData({
        method: 'POST',
        endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
        service: 'note-taker/settings',
        credentials: 'include',
        body: JSON.stringify({
          name: payload.name,
          system_name: payload.system_name,
          description: payload.description || '',
          config: payload.config || defaultSettings(),
        }),
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
        },
      })

      if (response?.error || !response?.ok) {
        throw new Error(response?.error || 'Failed to create note taker settings')
      }

      const data = await response.json()
      const record = normalizeSettingsPayload(data)[0]
      if (record) {
        commit('addNoteTakerRecord', record)
      }
      return record
    } finally {
      commit('setNoteTakerLoading', false)
    }
  },

  async fetchNoteTakerSettingsById({ commit, rootGetters }: any, settingsId: string) {
    commit('setNoteTakerLoading', true)
    try {
      const response = await fetchData({
        method: 'GET',
        endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
        service: `note-taker/settings/${encodeURIComponent(settingsId)}`,
        credentials: 'include',
        headers: {
          Accept: 'application/json',
        },
      })

      if (response?.error || !response?.ok) {
        console.error('Failed to fetch note taker settings:', response?.error)
        return null
      }

      const data = await response.json()
      const record = normalizeSettingsPayload(data)[0]
      if (!record) {
        return null
      }

      commit('upsertNoteTakerRecord', record)
      commit('setNoteTakerActiveSettingsKey', record.key)
      commit('setNoteTakerSettings', record.config)
      return record
    } finally {
      commit('setNoteTakerLoading', false)
    }
  },

  updateNoteTakerSetting({ commit }: any, payload: { path: string; value: any }) {
    commit('updateNoteTakerSetting', payload)
  },

  selectNoteTakerSettings({ commit, state }: any, key: string) {
    const record = state.settingsRecords.find(
      (item: NoteTakerSettingsRecord) => item.key === key
    )
    if (!record) return
    commit('setNoteTakerActiveSettingsKey', key)
    commit('setNoteTakerSettings', record.config)
  },

  selectNoteTakerSettingsById({ commit, state }: any, id: string) {
    const record = state.settingsRecords.find(
      (item: NoteTakerSettingsRecord) => item.id === id || item.system_name === id || item.key === id
    )
    if (!record) return null
    commit('setNoteTakerActiveSettingsKey', record.key)
    commit('setNoteTakerSettings', record.config)
    return record
  },

  updateNoteTakerRecordMeta(
    { commit, state }: any,
    payload: { name?: string; description?: string; system_name?: string }
  ) {
    commit('setNoteTakerRecordMeta', {
      key: state.activeSettingsKey,
      name: payload.name,
      description: payload.description,
      system_name: payload.system_name,
    })
  },
}

export default {
  state: state(),
  getters,
  mutations,
  actions,
}
