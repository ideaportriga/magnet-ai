import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchData } from '@shared'
import { useAppStore } from './appStore'

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

export const usePromptQueueStore = defineStore('promptQueue', () => {
  const appStore = useAppStore()

  const promptQueueConfigs = ref<PromptQueueConfigRecord[]>([])
  const selectedPromptQueueConfig = ref<PromptQueueConfigRecord | null>(null)
  const promptQueueLoading = ref(false)
  const executeDrawerOpen = ref(false)

  async function fetchPromptQueueConfigs(forceRefresh = false) {
    if (promptQueueConfigs.value.length > 0 && forceRefresh !== true) return

    promptQueueLoading.value = true
    try {
      const response = await fetchData({
        method: 'GET',
        endpoint: appStore.config?.api?.aiBridge?.urlAdmin,
        service: 'prompt-queue/configs?limit=1000',
        credentials: 'include',
      })

      if (response?.error) {
        promptQueueConfigs.value = []
        return
      }

      const data = await response.json()
      const configsArray = Array.isArray(data)
        ? data
        : data?.items || data?.data || data?.configs || []

      promptQueueConfigs.value = configsArray
    } catch (error) {
      promptQueueConfigs.value = []
    } finally {
      promptQueueLoading.value = false
    }
  }

  async function createPromptQueueConfig({
    name,
    system_name,
    description,
    config,
  }: {
    name: string
    system_name: string
    description?: string
    config?: PromptQueueConfigData
  }) {
    promptQueueLoading.value = true
    try {
      const response = await fetchData({
        method: 'POST',
        endpoint: appStore.config?.api?.aiBridge?.urlAdmin,
        service: 'prompt-queue/configs',
        credentials: 'include',
        body: JSON.stringify({ name, system_name, description, config: config || { steps: [] } }),
        headers: { 'Content-Type': 'application/json' },
      })

      if (response?.error) {
        throw new Error(response.error)
      }

      const data = await response.json()
      promptQueueConfigs.value.push(data)
      return data
    } finally {
      promptQueueLoading.value = false
    }
  }

  async function fetchPromptQueueConfigById(configId: string) {
    promptQueueLoading.value = true
    try {
      const response = await fetchData({
        method: 'GET',
        endpoint: appStore.config?.api?.aiBridge?.urlAdmin,
        service: `prompt-queue/configs/${configId}`,
        credentials: 'include',
      })

      if (response?.error) {
        throw new Error(response.error)
      }

      const data = await response.json()
      selectedPromptQueueConfig.value = data
      return data
    } finally {
      promptQueueLoading.value = false
    }
  }

  async function updatePromptQueueConfig({
    configId,
    updates,
  }: {
    configId: string
    updates: { name?: string; description?: string; system_name?: string; config?: PromptQueueConfigData }
  }) {
    promptQueueLoading.value = true
    try {
      const response = await fetchData({
        method: 'PATCH',
        endpoint: appStore.config?.api?.aiBridge?.urlAdmin,
        service: `prompt-queue/configs/${configId}`,
        credentials: 'include',
        body: JSON.stringify(updates),
        headers: { 'Content-Type': 'application/json' },
      })

      if (response?.error) {
        throw new Error(response.error)
      }

      const data = await response.json()
      const index = promptQueueConfigs.value.findIndex((c) => c.id === data.id)
      if (index !== -1) {
        promptQueueConfigs.value.splice(index, 1, data)
      }
      selectedPromptQueueConfig.value = data
      return data
    } finally {
      promptQueueLoading.value = false
    }
  }

  async function executePromptQueue({ configId, input }: { configId: string; input: Record<string, string> }) {
    const response = await fetchData({
      method: 'POST',
      endpoint: appStore.config?.api?.aiBridge?.urlAdmin,
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
  }

  async function deletePromptQueueConfig(configId: string) {
    promptQueueLoading.value = true
    try {
      const response = await fetchData({
        method: 'DELETE',
        endpoint: appStore.config?.api?.aiBridge?.urlAdmin,
        service: `prompt-queue/configs/${configId}`,
        credentials: 'include',
      })

      if (response?.error) {
        throw new Error(response.error)
      }

      promptQueueConfigs.value = promptQueueConfigs.value.filter((c) => c.id !== configId)
      selectedPromptQueueConfig.value = null
    } finally {
      promptQueueLoading.value = false
    }
  }

  return {
    // state
    promptQueueConfigs,
    selectedPromptQueueConfig,
    promptQueueLoading,
    executeDrawerOpen,
    // actions
    fetchPromptQueueConfigs,
    createPromptQueueConfig,
    fetchPromptQueueConfigById,
    updatePromptQueueConfig,
    executePromptQueue,
    deletePromptQueueConfig,
  }
})
