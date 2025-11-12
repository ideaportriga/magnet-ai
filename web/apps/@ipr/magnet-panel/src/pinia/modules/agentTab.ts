import { defineStore } from 'pinia'
import { useAiApps, useMainStore } from '@/pinia'
import { fetchData } from '@shared'

interface AgentTabState {
  answersLoading: boolean
  conversationId: string | null
}

const agentTab = defineStore('agentTab', {
  state: (): AgentTabState => ({
    answersLoading: false,
    conversationId: null,
  }),
  getters: {
    config: (): any => {
      const mainStore = useMainStore()
      return mainStore.config
    },
    endpoint: (): string => {
      const mainStore = useMainStore()
      return mainStore.endpoint.panel
    },
  },
  actions: {
    async getLastRelevantConversation(client_id: string) {
      const mainStore = useMainStore()
      const endpoint = this.endpoint
      const credentials = mainStore.config?.credentials
      const encodedClientId = encodeURIComponent(client_id)

      this.answersLoading = true
      const response = await fetchData({
        method: 'GET',
        endpoint,
        service: `agent_conversations/client/${encodedClientId}`,
        credentials,
        headers: {
          'Content-Type': 'application/json',
        },
      })
      this.answersLoading = false

      if (response?.error) {
        return
      }
      const answer = await response.json()
      return answer
    },
    async createConversation({ agent, user_message_content, client_id }: { agent: string; user_message_content: string; client_id: string }) {
      const mainStore = useMainStore()
      const aiApp = useAiApps()
      const aiAppSystemName = aiApp?.app?.system_name

      const endpoint = this.endpoint
      const service = 'agent_conversations'
      const credentials = mainStore.config?.credentials

      this.answersLoading = true

      const response = await fetchData({
        method: 'POST',
        endpoint,
        service: service,
        credentials,
        body: JSON.stringify({
          agent,
          user_message_content,
          client_id,
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
          text: `Error calling create conversation service`,
        })
        return
      }

      const answer = await response.json()
      return answer
    },
    async addUserMessageToConversation({
      conversation_id,
      user_message_content,
      action_call_confirmations,
    }: {
      conversation_id: string
      user_message_content: string
      action_call_confirmations: string[]
    }) {
      const mainStore = useMainStore()
      const aiApp = useAiApps()
      const aiAppSystemName = aiApp?.app?.system_name

      const endpoint = this.endpoint
      const service = `agent_conversations/${conversation_id}/messages`
      const credentials = mainStore.config?.credentials

      this.answersLoading = true

      const body: any = {}
      if (user_message_content) {
        body.user_message_content = user_message_content
      }
      if (action_call_confirmations) {
        body.action_call_confirmations = action_call_confirmations
      }

      const response = await fetchData({
        method: 'POST',
        endpoint,
        service,
        credentials,
        body: JSON.stringify(body),
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
          text: `Error calling new conversation message service`,
        })
        return
      }

      const answer = await response.json()
      return answer
    },
    async sendFeedback({
      conversation_id,
      message_id,
      feedback,
    }: {
      conversation_id: string
      message_id: string
      feedback: { type: string; reason: string; comment: string }
    }) {
      ///api/user/agent_conversations/67a5e080efaeaa76ce0844f8/messages/ac499b7b-e4ca-478d-a2d5-f006ff1ffbe5/feedback
      const mainStore = useMainStore()

      const endpoint = this.endpoint
      const service = `agent_conversations/${conversation_id}/messages/${message_id}/feedback`
      const credentials = mainStore.config?.credentials

      return await fetchData({
        method: 'POST',
        endpoint,
        service,
        credentials,
        body: JSON.stringify(feedback),
        headers: {
          'Content-Type': 'application/json',
        },
      })
        .then((res) => true)
        .catch((err) => {
          mainStore.setErrorMessage({
            technicalError: err,
            text: `Error sending feedback`,
          })
          return false
        })
    },
    async reportCopyUsage({ conversation_id, message_id }: { conversation_id: string; message_id: string }) {
      const mainStore = useMainStore()

      const endpoint = this.endpoint
      const service = `agent_conversations/${conversation_id}/messages/${message_id}/copy`
      const credentials = mainStore.config?.credentials

      await fetchData({
        method: 'POST',
        endpoint,
        service,
        credentials,
      })
    },
  },
})

export default agentTab
