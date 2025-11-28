import { defineStore } from 'pinia'
import { useMainStore, useModel } from '@/pinia'
import { fetchData } from '@shared'

const useChatCompletion = defineStore('chatCompletion', {
  state: () => ({
    enhancedTextLoading: false,
  }),
  getters: {
    endpoint: (): string => {
      const mainStore = useMainStore()
      return mainStore.config?.api?.aiBridge?.urlUser ?? ''
    },
    defaultInputs: (): { model: string; temperature: number; topP: number } => {
      return {
        model: 'gpt-35-turbo',
        temperature: 1,
        topP: 1,
      }
    },
  },
  actions: {
    async parsePdf(file: File) {
      const mainStore = useMainStore()
      const formData = new FormData()
      formData.append('file', file)
      return await fetchData({
        method: 'POST',
        endpoint: this.endpoint,
        credentials: mainStore.config?.credentials,
        service: `utils/parse-pdf`,
        body: formData,
        headers: {},
      })
        .then((response) => {
          if (response.ok) return response.json()
          if (response.error) throw response
        })
        .then((pdfContent) => {
          return pdfContent
        })
        .catch((response) => {
          mainStore.setErrorMessage({
            technicalError: response?.error,
            text: `Error parsing PDF file collection`,
          })
        })
    },
    async parseOpenapiSpec(file: File) {
      const formData = new FormData()
      formData.append('file', file)
      const mainStore = useMainStore()
      if (!file) {
        mainStore.setErrorMessage({
          technicalError: 'File is missing',
          text: `Error parsing OpenAPI spec file`,
        })
      }

      return await fetchData({
        method: 'POST',
        endpoint: this.endpoint,
        credentials: mainStore.config?.credentials,
        service: 'experimental/parse-openapi-spec',
        body: formData,
        headers: {},
      })
        .then((response) => {
          if (response.ok) return response.json()
          if (response.error) throw response
        })
        .then((pdfContent) => {
          return pdfContent
        })
        .catch((response) => {
          mainStore.setErrorMessage({
            technicalError: response?.error,
            text: `Error parsing OpenAPI spec file`,
          })
        })
    },
    async chatCompletionsWithOpenapiFunctions({ data, signal }: { data: any; signal: AbortSignal }) {
      const mainStore = useMainStore()
      return await fetchData({
        method: 'POST',
        endpoint: this.endpoint,
        credentials: mainStore.config?.credentials,
        service: 'experimental/chat-completions-with-openapi-functions',
        body: JSON.stringify(data),
        headers: {
          'Content-Type': 'application/json',
        },
        signal,
      })
        .then((response) => {
          if (response.ok) return response.json()
          if (response.error) throw response
        })
        .then((pdfContent) => {
          return pdfContent
        })
        .catch((response) => {
          mainStore.setErrorMessage({
            technicalError: response?.error,
            text: `Error running chat completion`,
          })
        })
    },
    async chatCompletionsWithAssistantTools({ data, signal }: { data: any; signal: AbortSignal }) {
      const mainStore = useMainStore()
      return await fetchData({
        method: 'POST',
        endpoint: this.endpoint,
        credentials: mainStore.config?.credentials,
        service: 'experimental/chat-completions-with-assistant-tools',
        body: JSON.stringify(data),
        headers: {
          'Content-Type': 'application/json',
        },
        signal,
      })
        .then((response) => {
          if (response.ok) return response.json()
          if (response.error) throw response
        })
        .then((pdfContent) => {
          return pdfContent
        })
        .catch((response) => {
          mainStore.setErrorMessage({
            technicalError: response?.error,
            text: `Error running chat completion`,
          })
        })
    },
    async enhanceText({
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
      temperature: number
      model: string
      topP: number
      maxTokens: number
      response_format: string
      system_name_for_model: string
    }) {
      const mainStore = useMainStore()
      const modelStore = useModel()
      const defaultModel = (modelStore.items || []).find((el: any) => el?.is_default && el?.type == 'prompts')
      // const config = getters.config?.chatCompletion || {}

      const inputs: any = {
        messages: [
          { role: 'system', content: prompt },
          { role: 'user', content: text },
        ],
      }
      if (temperature) inputs['temperature'] = temperature
      if (model || defaultModel) inputs['model'] = model ? model : defaultModel?.model
      if (topP) inputs['topP'] = topP
      if (maxTokens) inputs['maxTokens'] = maxTokens
      if (response_format) inputs['response_format'] = response_format
      if (system_name_for_model) inputs['system_name_for_model'] = system_name_for_model

      this.enhancedTextLoading = true
      const response = await fetchData({
        endpoint: this.endpoint,
        service: 'prompt_templates/test',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: mainStore.config?.credentials,
        body: JSON.stringify({
          ...this.defaultInputs,
          ...inputs,
        }),
      })

      this.enhancedTextLoading = false

      if (response?.error) {
        mainStore.setErrorMessage({
          technicalError: response?.error,
          text: `Error calling enhance text service`,
        })
      } else {
        const enhancement = await response.json()
        return enhancement?.['content'] ?? ''
      }
    },
  },
})

export default useChatCompletion
