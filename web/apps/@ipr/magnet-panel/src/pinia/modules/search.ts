import { defineStore } from 'pinia'
import { useAiApps, useMainStore } from '@/pinia'
import { fetchData } from '@shared'

interface SearchState {
  answers: SearchAnswer[]
  answersLoading: boolean
  searchPrompt: string
  service: string
}

interface SearchAnswer {
  prompt: string
  results: any[]
  answer?: any
}

const useSearch = defineStore('search', {
  state: (): SearchState => ({
    answers: [],
    answersLoading: false,
    searchPrompt: '',
    service: 'search',
  }),
  getters: {
    config: (): any => {
      const mainStore = useMainStore()
      return mainStore.config
    },
    ragToolCodeDefault: (): string | null => {
      return null
    },
    retrievalToolCodeDefault: (): string | null => {
      return null
    },
  },
  actions: {
    clearAnswers() {
      this.answers = []
    },
    setAnswers(answer: SearchAnswer) {
      this.answers = [answer, ...this.answers]
    },
    async getAnswerRagExecute(ragToolCode = null) {
      const mainStore = useMainStore()
      const aiApp = useAiApps()
      const aiAppSystemName = aiApp?.app?.system_name

      const prompt = this.searchPrompt
      const service = 'execute/rag_tool'
      const endpoint = mainStore.endpoint.panel
      const credentials = mainStore.config?.credentials
      const ragToolCodeDefault = this.ragToolCodeDefault || 'RAG_TOOL_TEST'

      this.answersLoading = true

      const response = await fetchData({
        method: 'POST',
        endpoint,
        service,
        credentials,
        body: JSON.stringify({
          user_message: prompt,
          system_name: ragToolCode || ragToolCodeDefault,
        }),
        headers: {
          'Content-Type': 'application/json',
          'X-Consumer-Name': aiAppSystemName || '',
          'X-Source': 'Runtime AI App',
        },
      })
      this.answersLoading = false

      if (response?.error) {
        mainStore.setErrorMessage({
          technicalError: response?.error,
          text: `Error calling search service`,
        })
      } else {
        const answer = await response.json()
        this.setAnswers({
          prompt,
          ...answer,
        })
      }
    },
    async getAnswerRetrievalExecute(retrievalToolCode = null) {
      const mainStore = useMainStore()
      const aiApp = useAiApps()
      const aiAppSystemName = aiApp?.app?.system_name

      const prompt = this.searchPrompt
      const service = 'execute/retrieval_tool'
      const endpoint = mainStore.endpoint.panel
      const credentials = mainStore.config?.credentials
      const retrievalToolCodeDefault = this.retrievalToolCodeDefault || 'TEST_RETRIEVAL'

      this.answersLoading = true

      const response = await fetchData({
        method: 'POST',
        endpoint,
        service,
        credentials,
        body: JSON.stringify({
          user_message: prompt,
          system_name: retrievalToolCode || retrievalToolCodeDefault,
        }),
        headers: {
          'Content-Type': 'application/json',
          'X-Consumer-Name': aiAppSystemName || '',
          'X-Source': 'Runtime AI App',
        },
      })

      this.answersLoading = false

      if (response?.error) {
        mainStore.setErrorMessage({
          technicalError: response?.error,
          text: `Error calling get answer retrieval service`,
        })
      } else {
        const answer = await response.json()
        this.setAnswers({
          prompt,
          ...answer,
        })
      }
    },
    async sendFeedback(
      { trace_id, analytics_id }: { trace_id: string; analytics_id: string },
      feedback: { type: string; reason?: string; comment?: string }
    ) {
      const mainStore = useMainStore()
      const endpoint = mainStore.endpoint.panel
      const credentials = mainStore.config?.credentials
      const service = 'telemetry/tool_response_feedback'
      await fetchData({
        method: 'POST',
        endpoint,
        service,
        credentials,
        body: JSON.stringify({ trace_id, analytics_id, feedback }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      this.answers = this.answers.map((answer: any) => {
        if (answer.trace_id === trace_id) {
          answer.feedback = feedback
        }
        return answer
      })
    },
    async reportCopyUsage({ trace_id, analytics_id }: { trace_id: string; analytics_id: string }) {
      const mainStore = useMainStore()
      const endpoint = mainStore.endpoint.panel
      const credentials = mainStore.config?.credentials
      const service = 'telemetry/tool_response_copy'
      await fetchData({
        method: 'POST',
        endpoint,
        service,
        credentials,
        body: JSON.stringify({ trace_id, analytics_id }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
    },
  },
})

export default useSearch
