import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchData } from '@shared'
import { useAppStore } from './appStore'

export const useSpecificationsStore = defineStore('specifications', () => {
  const appStore = useAppStore()

  const specifications = ref<any[]>([])
  const enhancedTextLoading = ref(false)

  const specificationsWithId = computed(() =>
    specifications.value.map((val, idx) => ({ id: idx, ...val }))
  )

  async function getSpecifications() {
    const endpoint = appStore.config?.specifications?.endpoint
    const service = appStore.config?.specifications?.service

    const response = await fetchData({
      endpoint,
      service,
      method: 'GET',
      headers: { 'ngrok-skip-browser-warning': '69420' },
    })

    if (response?.error) {
      appStore.setErrorMessage({
        technicalError: response?.error,
        text: 'Error calling specifications service',
      })
      return false
    } else {
      const json = await response.json()
      specifications.value = json
      return true
    }
  }

  async function upsertSpecification({ id = '', specification }: { id?: string; specification: any }) {
    const endpoint = appStore.config?.specifications?.endpoint
    const service = appStore.config?.specifications?.service

    const response = await fetchData({
      endpoint,
      service: `${service}${id ? `/${id}` : ''}`,
      method: id ? 'PUT' : 'POST',
      headers: {
        'ngrok-skip-browser-warning': '69420',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(specification),
    })

    if (response?.error) {
      appStore.setErrorMessage({
        technicalError: response?.error,
        text: 'Error calling specifications service',
      })
    } else {
      const json = await response.json()
      return json
    }
  }

  async function removeSpecification({ id = '' }: { id?: string }) {
    const endpoint = appStore.config?.specifications?.endpoint
    const service = appStore.config?.specifications?.service

    const response = await fetchData({
      endpoint,
      service: `${service}/${id}`,
      method: 'DELETE',
      headers: { 'ngrok-skip-browser-warning': '69420' },
    })

    if (response?.error) {
      appStore.setErrorMessage({
        technicalError: response?.error,
        text: 'Error calling specifications service',
      })
      return false
    } else {
      return true
    }
  }

  async function enhanceText({
    text,
    prompt,
    temperature = 1,
    model,
    topP = 1,
    maxTokens,
    response_format,
    system_name_for_model,
  }: {
    text: string
    prompt: string
    temperature?: number
    model?: string
    topP?: number
    maxTokens?: number
    response_format?: any
    system_name_for_model?: string
  }) {
    const config = appStore.config?.chatCompletion || {} as any

    const inputs: Record<string, any> = {
      messages: [
        { role: 'system', content: prompt },
        { role: 'user', content: text },
      ],
    }
    if (temperature) inputs.temperature = temperature
    if (model) inputs.model = model
    if (topP) inputs.topP = topP
    if (maxTokens) inputs.maxTokens = maxTokens
    if (response_format) inputs.response_format = response_format
    if (system_name_for_model) inputs.system_name_for_model = system_name_for_model

    enhancedTextLoading.value = true

    const response = await fetchData({
      endpoint: config.endpoint,
      service: config.service,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ ...config.inputs, ...inputs }),
    })

    enhancedTextLoading.value = false

    if (response?.error) {
      appStore.setErrorMessage({
        technicalError: response?.error,
        text: 'Error calling enhance text service',
      })
      return ''
    } else {
      const enhancement = await response.json()
      return enhancement?.content ?? ''
    }
  }

  async function enhanceTextDetails({
    name,
    text,
    prompt,
    temperature = 1,
    model,
    topP = 1,
    maxTokens,
    response_format,
    system_name_for_model,
    system_name_for_prompt_template,
    prompt_template_variant,
  }: {
    name?: string
    text: string
    prompt: string
    temperature?: number
    model?: string
    topP?: number
    maxTokens?: number
    response_format?: any
    system_name_for_model?: string
    system_name_for_prompt_template?: string
    prompt_template_variant?: string
  }) {
    const config = appStore.config?.chatCompletion || {} as any

    const inputs: Record<string, any> = {
      messages: [
        { role: 'system', content: prompt },
        { role: 'user', content: text },
      ],
    }
    if (name) inputs.name = name
    if (temperature) inputs.temperature = temperature
    if (model) inputs.model = model
    if (topP) inputs.top_p = topP
    if (maxTokens) inputs.max_tokens = maxTokens
    if (response_format) inputs.response_format = response_format
    if (system_name_for_model) inputs.system_name_for_model = system_name_for_model
    if (system_name_for_prompt_template) inputs.system_name_for_prompt_template = system_name_for_prompt_template
    if (prompt_template_variant) inputs.prompt_template_variant = prompt_template_variant

    enhancedTextLoading.value = true

    const response = await fetchData({
      endpoint: config.endpoint,
      service: config.service,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ ...config.inputs, ...inputs }),
    })

    enhancedTextLoading.value = false

    if (response?.error) {
      appStore.setErrorMessage({
        technicalError: response?.error,
        text: 'Error calling enhance text details service',
      })
      return ''
    } else {
      const enhancement = await response.json()
      enhancement.inputs = inputs
      return enhancement
    }
  }

  return {
    // state
    specifications,
    enhancedTextLoading,
    // computed
    specificationsWithId,
    // actions
    getSpecifications,
    upsertSpecification,
    removeSpecification,
    enhanceText,
    enhanceTextDetails,
  }
})
