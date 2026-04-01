import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAppStore } from './appStore'
import { getApiClient } from '@/api'

export const useConversationStore = defineStore('conversation', () => {
  const appStore = useAppStore()

  const conversation = ref<Record<string, unknown> | null>(null)
  const loading = ref(false)

  async function getConversation({ conversation_id }: { conversation_id: string }) {
    loading.value = true
    try {
      const client = getApiClient()
      const data = await client.get<Record<string, unknown>>(`agents/conversations/${conversation_id}`)
      conversation.value = data
    } catch (error) {
      appStore.setErrorMessage({
        text: 'Error loading conversation',
        technicalError: error instanceof Error ? error.message : String(error),
      })
    } finally {
      loading.value = false
    }
  }

  async function closeConversation(conversationId: string) {
    loading.value = true
    try {
      const client = getApiClient()
      await client.post('agents/post_process', { conversation_id: conversationId })
      await getConversation({ conversation_id: conversationId })
    } catch (error) {
      appStore.setErrorMessage({
        text: 'Error closing conversation',
        technicalError: error instanceof Error ? error.message : String(error),
      })
    } finally {
      loading.value = false
    }
  }

  return {
    conversation,
    loading,
    getConversation,
    closeConversation,
  }
})
