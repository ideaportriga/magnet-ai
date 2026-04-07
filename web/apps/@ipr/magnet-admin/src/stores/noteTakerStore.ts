import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchData } from '@shared'
import { useAppStore } from './appStore'

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
  accept_commands_from_non_organizer: boolean
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

const DEFAULT_SETTINGS_KEY = 'default'

const defaultSettings = (): NoteTakerSettings => ({
  subscription_recordings_ready: false,
  pipeline_id: '',
  send_number_of_speakers: false,
  accept_commands_from_non_organizer: false,
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

export const useNoteTakerStore = defineStore('noteTaker', () => {
  const appStore = useAppStore()

  const settings = ref<NoteTakerSettings>(defaultSettings())
  const settingsRecords = ref<NoteTakerSettingsRecord[]>([])
  const activeSettingsKey = ref<string | null>(null)
  const loading = ref(false)
  const activeListTab = ref('configurations')
  const activePreviewJobId = ref<string | null>(null)
  const previewJobs = ref<PreviewJob[]>([])
  const previewJobsLoading = ref(false)
  const runtimeStatus = ref<Record<string, { runtime_loaded: boolean; has_credentials: boolean }>>({})

  const activeRecord = computed(() =>
    settingsRecords.value.find((record) => record.key === activeSettingsKey.value) || null
  )

  function updateSetting({ path, value }: { path: string; value: any }) {
    const keys = path.split('.')
    let target: any = settings.value

    for (let i = 0; i < keys.length - 1; i++) {
      if (!(keys[i] in target) || target[keys[i]] === null) target[keys[i]] = {}
      target = target[keys[i]]
    }
    target[keys[keys.length - 1]] = value

    const key = activeSettingsKey.value
    if (key) {
      const recordIndex = settingsRecords.value.findIndex((record) => record.key === key)
      if (recordIndex >= 0) {
        settingsRecords.value[recordIndex] = {
          ...settingsRecords.value[recordIndex],
          config: mergeSettings(settings.value),
        }
      }
    }
  }

  function setRecordMeta(payload: {
    key: string | null
    name?: string
    description?: string
    system_name?: string
    provider_system_name?: string | null
    superuser_id?: string | null
  }) {
    if (!payload.key) return
    const index = settingsRecords.value.findIndex((record) => record.key === payload.key)
    if (index < 0) return
    settingsRecords.value[index] = {
      ...settingsRecords.value[index],
      name: payload.name ?? settingsRecords.value[index].name,
      description: payload.description ?? settingsRecords.value[index].description,
      system_name: payload.system_name ?? settingsRecords.value[index].system_name,
      ...(payload.provider_system_name !== undefined ? { provider_system_name: payload.provider_system_name } : {}),
      ...(payload.superuser_id !== undefined ? { superuser_id: payload.superuser_id } : {}),
    }
  }

  function selectSettings(key: string) {
    const record = settingsRecords.value.find((item) => item.key === key)
    if (!record) return
    activeSettingsKey.value = key
    settings.value = mergeSettings(record.config)
  }

  function selectSettingsById(id: string) {
    const record = settingsRecords.value.find(
      (item) => item.id === id || item.system_name === id || item.key === id
    )
    if (!record) return null
    activeSettingsKey.value = record.key
    settings.value = mergeSettings(record.config)
    return record
  }

  function updateRecordMeta(payload: { name?: string; description?: string; system_name?: string }) {
    setRecordMeta({
      key: activeSettingsKey.value,
      name: payload.name,
      description: payload.description,
      system_name: payload.system_name,
    })
  }

  function upsertPreviewJob(job: PreviewJob) {
    const index = previewJobs.value.findIndex((j) => j.id === job.id)
    if (index >= 0) previewJobs.value.splice(index, 1, job)
    else previewJobs.value.unshift(job)
  }

  async function fetchSettings(forceRefresh = false) {
    loading.value = true
    try {
      if (settingsRecords.value.length > 0 && !forceRefresh) return
      const response = await fetchData({
        method: 'GET',
        endpoint: appStore.config?.api?.aiBridge?.urlAdmin,
        service: 'note-taker/settings',
        credentials: 'include',
        headers: { Accept: 'application/json' },
      })

      if (response?.error || !response?.ok) return

      const data = await response.json()
      const records = normalizeSettingsPayload(data)
      settingsRecords.value = records

      if (!records.length) {
        activeSettingsKey.value = null
        settings.value = defaultSettings()
        return
      }

      let key = activeSettingsKey.value
      if (!key || !records.find((record: any) => record.key === key)) {
        key = records[0]?.key || null
      }
      activeSettingsKey.value = key
      const active = records.find((record: any) => record.key === key)
      settings.value = active?.config || defaultSettings()
    } catch (error) {
      // silent
    } finally {
      loading.value = false
    }
  }

  async function saveSettings() {
    loading.value = true
    try {
      const record = settingsRecords.value.find(
        (r) => r.key === activeSettingsKey.value
      )
      const recordId = record?.id || record?.system_name
      const service = recordId
        ? `note-taker/settings/${encodeURIComponent(recordId)}`
        : 'note-taker/settings'

      const useRecordPayload = Boolean(
        record?.id || record?.system_name || record?.name || record?.description
      )

      const payload = useRecordPayload
        ? {
            id: record?.id,
            name: record?.name,
            system_name: record?.system_name,
            description: record?.description,
            config: settings.value,
            provider_system_name: record?.provider_system_name || null,
            superuser_id: record?.superuser_id || null,
          }
        : settings.value

      const response = await fetchData({
        method: 'PUT',
        endpoint: appStore.config?.api?.aiBridge?.urlAdmin,
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
        const normalized = normalizeSettingsPayload(data)[0]
        if (normalized) {
          const idx = settingsRecords.value.findIndex((item) => {
            if (normalized.id && item.id === normalized.id) return true
            if (normalized.system_name && item.system_name === normalized.system_name) return true
            return item.key === normalized.key
          })
          if (idx >= 0) settingsRecords.value.splice(idx, 1, normalized)
          else settingsRecords.value.push(normalized)
          activeSettingsKey.value = normalized.key
          settings.value = normalized.config
        }
      } catch {
        // keep current state
      }
    } finally {
      loading.value = false
    }
  }

  async function createSettings(payload: {
    name: string
    system_name: string
    description?: string
    config?: NoteTakerSettings
  }) {
    loading.value = true
    try {
      const response = await fetchData({
        method: 'POST',
        endpoint: appStore.config?.api?.aiBridge?.urlAdmin,
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
      if (record) settingsRecords.value.push(record)
      return record
    } finally {
      loading.value = false
    }
  }

  async function fetchSettingsById(settingsId: string) {
    loading.value = true
    try {
      const response = await fetchData({
        method: 'GET',
        endpoint: appStore.config?.api?.aiBridge?.urlAdmin,
        service: `note-taker/settings/${encodeURIComponent(settingsId)}`,
        credentials: 'include',
        headers: { Accept: 'application/json' },
      })

      if (response?.error || !response?.ok) return null

      const data = await response.json()
      const record = normalizeSettingsPayload(data)[0]
      if (!record) return null

      const idx = settingsRecords.value.findIndex((item) => {
        if (record.id && item.id === record.id) return true
        if (record.system_name && item.system_name === record.system_name) return true
        return item.key === record.key
      })
      if (idx >= 0) settingsRecords.value.splice(idx, 1, record)
      else settingsRecords.value.push(record)

      activeSettingsKey.value = record.key
      settings.value = record.config
      return record
    } finally {
      loading.value = false
    }
  }

  async function deleteSettings(settingsId: string) {
    loading.value = true
    try {
      const response = await fetchData({
        method: 'DELETE',
        endpoint: appStore.config?.api?.aiBridge?.urlAdmin,
        service: `note-taker/settings/${encodeURIComponent(settingsId)}`,
        credentials: 'include',
        headers: { Accept: 'application/json' },
      })

      if (response?.error || !response?.ok) {
        throw new Error(response?.error || 'Failed to delete note taker settings')
      }

      const record = settingsRecords.value.find(
        (r) => r.id === settingsId || r.system_name === settingsId || r.key === settingsId
      )
      if (record) {
        settingsRecords.value = settingsRecords.value.filter((r) => r.key !== record.key)
      }
    } finally {
      loading.value = false
    }
  }

  async function reloadRuntime(settingsId: string) {
    const response = await fetchData({
      method: 'POST',
      endpoint: appStore.config?.api?.aiBridge?.urlAdmin,
      service: `note-taker/settings/${encodeURIComponent(settingsId)}/reload`,
      credentials: 'include',
      headers: { Accept: 'application/json' },
    })

    if (response?.error || !response?.ok) {
      throw new Error(response?.error || 'Failed to reload runtime')
    }
    return response.json()
  }

  async function fetchRuntimeStatus(settingsId: string) {
    try {
      const response = await fetchData({
        method: 'GET',
        endpoint: appStore.config?.api?.aiBridge?.urlAdmin,
        service: `note-taker/settings/${encodeURIComponent(settingsId)}/status`,
        credentials: 'include',
        headers: { Accept: 'application/json' },
      })

      if (!response?.ok) return null
      const data = await response.json()
      runtimeStatus.value = { ...runtimeStatus.value, [settingsId]: data }
      return data
    } catch {
      return null
    }
  }

  async function runPreview(payload: {
    settingsId: string
    sourceUrl?: string
    file?: File
    participants?: string[]
    sttModelSystemName?: string
  }) {
    const endpoint = appStore.config?.api?.aiBridge?.urlAdmin?.replace(/\/$/, '')
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
  }

  async function fetchPreviewJobs(settingsId: string) {
    previewJobsLoading.value = true
    try {
      const response = await fetchData({
        method: 'GET',
        endpoint: appStore.config?.api?.aiBridge?.urlAdmin,
        service: `note-taker/jobs/${encodeURIComponent(settingsId)}`,
        credentials: 'include',
        headers: { Accept: 'application/json' },
      })
      if (!response?.ok) return []
      const data = await response.json()
      const jobs = Array.isArray(data) ? data : []
      previewJobs.value = jobs
      return jobs
    } finally {
      previewJobsLoading.value = false
    }
  }

  async function fetchPreviewJobStatus({ settingsId, jobId }: { settingsId: string; jobId: string }) {
    const response = await fetchData({
      method: 'GET',
      endpoint: appStore.config?.api?.aiBridge?.urlAdmin,
      service: `note-taker/jobs/${encodeURIComponent(settingsId)}/${encodeURIComponent(jobId)}`,
      credentials: 'include',
      headers: { Accept: 'application/json' },
    })
    if (!response?.ok) return null
    const job = await response.json()
    upsertPreviewJob(job)
    return job
  }

  async function rerunPreviewPostprocessing(payload: {
    settingsId: string
    jobId: string
    speakerMapping: Record<string, string>
    extraKeyterms: string[]
  }) {
    const response = await fetchData({
      method: 'POST',
      endpoint: appStore.config?.api?.aiBridge?.urlAdmin,
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
  }

  return {
    // state
    settings,
    settingsRecords,
    activeSettingsKey,
    activeListTab,
    activePreviewJobId,
    loading,
    previewJobs,
    previewJobsLoading,
    runtimeStatus,
    // computed
    activeRecord,
    // actions
    updateSetting,
    setRecordMeta,
    selectSettings,
    selectSettingsById,
    updateRecordMeta,
    upsertPreviewJob,
    fetchSettings,
    saveSettings,
    createSettings,
    fetchSettingsById,
    deleteSettings,
    reloadRuntime,
    fetchRuntimeStatus,
    runPreview,
    fetchPreviewJobs,
    fetchPreviewJobStatus,
    rerunPreviewPostprocessing,
  }
})
