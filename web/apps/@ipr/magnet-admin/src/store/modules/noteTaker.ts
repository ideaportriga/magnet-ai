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
  title_template: string
  tool_system_name?: string
}

interface NoteTakerSettings {
  subscription_recordings_ready: boolean
  pipeline_id: string
  send_number_of_speakers: boolean
  create_knowledge_graph_embedding: boolean
  knowledge_graph_system_name: string
  keyterms: string
  integration: {
    confluence: ConfluenceIntegrationSettings
    salesforce: SalesforceIntegrationSettings
  }
  chapters: PromptSetting
  summary: PromptSetting
  insights: PromptSetting
  post_transcription: PromptSetting
}

export interface PreviewJob {
  id: string
  settings_id: string
  user_id: string | null
  source_url: string | null
  participants: string[] | null
  status: 'pending' | 'running' | 'transcribed' | 'completed' | 'failed' | 'rerunning'
  result: any | null
  created_at: string | null
  updated_at: string | null
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
  provider_system_name?: string | null
  superuser_id?: string | null
}

interface State {
  settings: NoteTakerSettings
  settingsRecords: NoteTakerSettingsRecord[]
  activeSettingsKey: string | null
  loading: boolean
  previewJobs: PreviewJob[]
  previewJobsLoading: boolean
  runtimeStatus: Record<string, { runtime_loaded: boolean; has_credentials: boolean }>
}

const DEFAULT_SETTINGS_KEY = 'default'

const defaultSettings = (): NoteTakerSettings => ({
  subscription_recordings_ready: false,
  pipeline_id: '',
  send_number_of_speakers: false,
  create_knowledge_graph_embedding: false,
  knowledge_graph_system_name: '',
  keyterms: '',
  integration: {
    confluence: {
      enabled: false,
      confluence_api_server: '',
      confluence_create_page_tool: '',
      space_key: '',
      parent_id: '',
      title_template: 'Meeting notes: {meeting_title} ({date})',
    },
    salesforce: {
      send_transcript_to_salesforce: false,
      salesforce_api_server: '',
      salesforce_stt_recording_tool: '',
    },
  },
  chapters: { enabled: false, prompt_template: '' },
  summary: { enabled: false, prompt_template: '' },
  insights: { enabled: false, prompt_template: '' },
  post_transcription: { enabled: false, prompt_template: '' },
})

const mergeSettings = (settings?: Partial<NoteTakerSettings> | null): NoteTakerSettings => {
  const defaults = defaultSettings()
  const incomingConfluence = ((settings?.integration as any)?.confluence || {}) as Record<string, any>
  const mergedConfluence: ConfluenceIntegrationSettings = {
    ...defaults.integration.confluence,
    ...incomingConfluence,
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
    chapters: { ...defaults.chapters, ...(settings?.chapters || {}) },
    summary: { ...defaults.summary, ...(settings?.summary || {}) },
    insights: { ...defaults.insights, ...(settings?.insights || {}) },
    post_transcription: { ...defaults.post_transcription, ...(settings?.post_transcription || {}) },
  }
}

const toSettingsConfig = (payload: any): NoteTakerSettings => {
  let normalized = payload
  if (typeof normalized === 'string') {
    try { normalized = JSON.parse(normalized) } catch { normalized = {} }
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
        : payload ? [payload] : []

  if (!items.length) return []

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
      provider_system_name: item?.provider_system_name || null,
      superuser_id: item?.superuser_id || null,
    }
  })
}

// state
const state = (): State => ({
  settings: defaultSettings(),
  settingsRecords: [],
  activeSettingsKey: null,
  loading: false,
  previewJobs: [],
  previewJobsLoading: false,
  runtimeStatus: {},
})

// getters
const getters = {
  noteTakerSettings: (state: State) => state.settings,
  noteTakerSettingsRecords: (state: State) => state.settingsRecords,
  noteTakerSettingsActiveKey: (state: State) => state.activeSettingsKey,
  noteTakerSettingsActiveRecord: (state: State) =>
    state.settingsRecords.find((record) => record.key === state.activeSettingsKey) || null,
  noteTakerLoading: (state: State) => state.loading,
  noteTakerPreviewJobs: (state: State) => state.previewJobs,
  noteTakerPreviewJobsLoading: (state: State) => state.previewJobsLoading,
  noteTakerRuntimeStatus: (state: State) => state.runtimeStatus,
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
    payload: {
      key: string | null
      name?: string
      description?: string
      system_name?: string
      provider_system_name?: string | null
      superuser_id?: string | null
    }
  ) {
    if (!payload.key) return
    const index = state.settingsRecords.findIndex((record) => record.key === payload.key)
    if (index < 0) return
    state.settingsRecords[index] = {
      ...state.settingsRecords[index],
      name: payload.name ?? state.settingsRecords[index].name,
      description: payload.description ?? state.settingsRecords[index].description,
      system_name: payload.system_name ?? state.settingsRecords[index].system_name,
      ...(payload.provider_system_name !== undefined ? { provider_system_name: payload.provider_system_name } : {}),
      ...(payload.superuser_id !== undefined ? { superuser_id: payload.superuser_id } : {}),
    }
  },
  setNoteTakerRecordConfig(state: State, payload: { key: string | null; config: NoteTakerSettings }) {
    if (!payload.key) return
    const index = state.settingsRecords.findIndex((record) => record.key === payload.key)
    if (index < 0) return
    state.settingsRecords[index] = { ...state.settingsRecords[index], config: mergeSettings(payload.config) }
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
    if (index >= 0) state.settingsRecords.splice(index, 1, record)
    else state.settingsRecords.push(record)
  },
  removeNoteTakerRecord(state: State, key: string) {
    state.settingsRecords = state.settingsRecords.filter((r) => r.key !== key)
  },
  updateNoteTakerSetting(state: State, { path, value }: { path: string; value: any }) {
    const keys = path.split('.')
    let target: any = state.settings

    for (let i = 0; i < keys.length - 1; i++) {
      if (!(keys[i] in target) || target[keys[i]] === null) target[keys[i]] = {}
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
  setPreviewJobs(state: State, jobs: PreviewJob[]) {
    state.previewJobs = jobs
  },
  upsertPreviewJob(state: State, job: PreviewJob) {
    const index = state.previewJobs.findIndex((j) => j.id === job.id)
    if (index >= 0) state.previewJobs.splice(index, 1, job)
    else state.previewJobs.unshift(job)
  },
  setPreviewJobsLoading(state: State, loading: boolean) {
    state.previewJobsLoading = loading
  },
  setRuntimeStatus(state: State, { key, status }: { key: string; status: any }) {
    state.runtimeStatus = { ...state.runtimeStatus, [key]: status }
  },
}

// actions
const actions = {
  async fetchNoteTakerSettings({ commit, state, rootGetters }: any, forceRefresh = false) {
    commit('setNoteTakerLoading', true)
    try {
      if (state.settingsRecords.length > 0 && !forceRefresh) return
      const response = await fetchData({
        method: 'GET',
        endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
        service: 'note-taker/settings',
        credentials: 'include',
        headers: { Accept: 'application/json' },
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
      if (!activeKey || !records.find((record: any) => record.key === activeKey)) {
        activeKey = records[0]?.key || null
      }
      commit('setNoteTakerActiveSettingsKey', activeKey)
      const activeRecord = records.find((record: any) => record.key === activeKey)
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
            provider_system_name: activeRecord?.provider_system_name || null,
            superuser_id: activeRecord?.superuser_id || null,
          }
        : state.settings

      const response = await fetchData({
        method: 'PUT',
        endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
        service,
        credentials: 'include',
        body: JSON.stringify(payload),
        headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      })

      if (response?.error || !response?.ok) {
        throw new Error(response?.error || 'Failed to save note taker settings')
      }

      try {
        const data = await response.json()
        const record = normalizeSettingsPayload(data)[0]
        if (record) {
          commit('upsertNoteTakerRecord', record)
          commit('setNoteTakerActiveSettingsKey', record.key)
          commit('setNoteTakerSettings', record.config)
        } else {
          commit('setNoteTakerRecordConfig', { key: state.activeSettingsKey, config: state.settings })
        }
      } catch {
        commit('setNoteTakerRecordConfig', { key: state.activeSettingsKey, config: state.settings })
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
        headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      })

      if (response?.error || !response?.ok) {
        throw new Error(response?.error || 'Failed to create note taker settings')
      }

      const data = await response.json()
      const record = normalizeSettingsPayload(data)[0]
      if (record) commit('addNoteTakerRecord', record)
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
        headers: { Accept: 'application/json' },
      })

      if (response?.error || !response?.ok) {
        console.error('Failed to fetch note taker settings:', response?.error)
        return null
      }

      const data = await response.json()
      const record = normalizeSettingsPayload(data)[0]
      if (!record) return null

      commit('upsertNoteTakerRecord', record)
      commit('setNoteTakerActiveSettingsKey', record.key)
      commit('setNoteTakerSettings', record.config)
      return record
    } finally {
      commit('setNoteTakerLoading', false)
    }
  },

  async deleteNoteTakerSettings({ commit, state, rootGetters }: any, settingsId: string) {
    commit('setNoteTakerLoading', true)
    try {
      const response = await fetchData({
        method: 'DELETE',
        endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
        service: `note-taker/settings/${encodeURIComponent(settingsId)}`,
        credentials: 'include',
        headers: { Accept: 'application/json' },
      })

      if (response?.error || !response?.ok) {
        throw new Error(response?.error || 'Failed to delete note taker settings')
      }

      // Remove from local store
      const record = state.settingsRecords.find(
        (r: NoteTakerSettingsRecord) => r.id === settingsId || r.system_name === settingsId || r.key === settingsId
      )
      if (record) commit('removeNoteTakerRecord', record.key)
    } finally {
      commit('setNoteTakerLoading', false)
    }
  },

  async reloadNoteTakerRuntime({ rootGetters }: any, settingsId: string) {
    const response = await fetchData({
      method: 'POST',
      endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
      service: `note-taker/settings/${encodeURIComponent(settingsId)}/reload`,
      credentials: 'include',
      headers: { Accept: 'application/json' },
    })

    if (response?.error || !response?.ok) {
      throw new Error(response?.error || 'Failed to reload runtime')
    }
    return response.json()
  },

  async fetchNoteTakerRuntimeStatus({ commit, rootGetters }: any, settingsId: string) {
    try {
      const response = await fetchData({
        method: 'GET',
        endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
        service: `note-taker/settings/${encodeURIComponent(settingsId)}/status`,
        credentials: 'include',
        headers: { Accept: 'application/json' },
      })

      if (!response?.ok) return null
      const data = await response.json()
      commit('setRuntimeStatus', { key: settingsId, status: data })
      return data
    } catch {
      return null
    }
  },

  updateNoteTakerSetting({ commit }: any, payload: { path: string; value: any }) {
    commit('updateNoteTakerSetting', payload)
  },

  selectNoteTakerSettings({ commit, state }: any, key: string) {
    const record = state.settingsRecords.find((item: NoteTakerSettingsRecord) => item.key === key)
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

  // ── Preview actions ────────────────────────────────────────────────────────

  async runNoteTakerPreview(
    { rootGetters }: any,
    payload: {
      settingsId: string
      sourceUrl?: string
      file?: File
      participants?: string[]
      sttModelSystemName?: string
    }
  ) {
    const endpoint = rootGetters.config?.api?.aiBridge?.urlAdmin?.replace(/\/$/, '')
    const baseUrl = `${endpoint}/note-taker/jobs/${encodeURIComponent(payload.settingsId)}`

    if (payload.file) {
      const formData = new FormData()
      formData.append('file', payload.file)
      if (payload.participants?.length) {
        formData.append('participants', payload.participants.join(','))
      }
      if (payload.sttModelSystemName) {
        formData.append('stt_model_system_name', payload.sttModelSystemName)
      }
      const response = await fetch(`${baseUrl}/run-upload`, { method: 'POST', body: formData, credentials: 'include' })
      if (!response.ok) throw new Error('Failed to start preview job')
      return response.json()
    }

    const url = `${baseUrl}/run`

    const response = await fetch(url, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({
        source_url: payload.sourceUrl || null,
        participants: payload.participants || [],
        stt_model_system_name: payload.sttModelSystemName || null,
      }),
    })
    if (!response.ok) throw new Error('Failed to start preview job')
    return response.json()
  },

  async fetchPreviewJobs({ commit, rootGetters }: any, settingsId: string) {
    commit('setPreviewJobsLoading', true)
    try {
      const response = await fetchData({
        method: 'GET',
        endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
        service: `note-taker/jobs/${encodeURIComponent(settingsId)}`,
        credentials: 'include',
        headers: { Accept: 'application/json' },
      })
      if (!response?.ok) return []
      const data = await response.json()
      const jobs = Array.isArray(data) ? data : []
      commit('setPreviewJobs', jobs)
      return jobs
    } finally {
      commit('setPreviewJobsLoading', false)
    }
  },

  async fetchPreviewJobStatus({ commit, rootGetters }: any, { settingsId, jobId }: { settingsId: string; jobId: string }) {
    const response = await fetchData({
      method: 'GET',
      endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
      service: `note-taker/jobs/${encodeURIComponent(settingsId)}/${encodeURIComponent(jobId)}`,
      credentials: 'include',
      headers: { Accept: 'application/json' },
    })
    if (!response?.ok) return null
    const job = await response.json()
    commit('upsertPreviewJob', job)
    return job
  },

  async rerunNoteTakerPreviewPostprocessing(
    { rootGetters }: any,
    payload: {
      settingsId: string
      jobId: string
      speakerMapping: Record<string, string>
      extraKeyterms: string[]
    }
  ) {
    const response = await fetchData({
      method: 'POST',
      endpoint: rootGetters.config?.api?.aiBridge?.urlAdmin,
      service: `note-taker/jobs/${encodeURIComponent(payload.settingsId)}/rerun`,
      credentials: 'include',
      body: JSON.stringify({
        job_id: payload.jobId,
        speaker_mapping: payload.speakerMapping,
        extra_keyterms: payload.extraKeyterms,
      }),
      headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
    })
    if (!response?.ok) throw new Error('Failed to rerun postprocessing')
    return response.json()
  },
}

export default {
  state: state(),
  getters,
  mutations,
  actions,
}
