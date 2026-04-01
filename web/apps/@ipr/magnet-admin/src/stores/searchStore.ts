import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { convertFiltersToFilterObject } from '@shared'
import { useAppStore } from './appStore'
import { getApiClient } from '@/api'

export const useSearchStore = defineStore('search', () => {
  const appStore = useAppStore()

  // --- UI State ---
  const searchPrompt = ref('')
  const metadataFilter = ref<Record<string, unknown>[]>([])
  const collectionList = ref<Record<string, unknown>[]>([])
  const collection = ref<string[]>([])
  const answersLoading = ref(false)
  const answers = ref<Record<string, unknown>[]>([])
  const feedback = ref<Record<string, unknown>>({})

  // Semantic search state (used by Collections/Drawer and details pages)
  const semanticSearchAnswers = ref<Record<string, unknown>[]>([])
  const semanticSearchLoading = ref(false)
  const semanticSearch = ref('')

  const publicCollectionList = computed(() => {
    return (
      collectionList.value
        ?.map(({ id, name, show_in_qa }: Record<string, unknown>) => ({
          id,
          value: name,
          label: name,
          show_in_qa,
        }))
        ?.filter(({ show_in_qa }: Record<string, unknown>) => show_in_qa) || []
    )
  })

  // --- Actions ---

  function clearAnswers() {
    answers.value = []
  }

  function setAnswers(answer: Record<string, unknown>) {
    answers.value = [answer, ...answers.value]
  }

  function setFeedback({ id, like, comment }: { id: string; like: boolean; comment: string }) {
    const answerIndex = answers.value.findIndex((answer) => answer.id === id)
    if (answerIndex >= 0) {
      answers.value[answerIndex].feedback = { like, comment }
    }
  }

  async function getAnswer() {
    const prompt = searchPrompt.value
    const collectionId =
      collection.value
        .map((value: unknown) => (typeof value === 'object' && value !== null ? (value as Record<string, unknown>).id : value))
        .join(',') || 'default_collection'

    answersLoading.value = true
    try {
      const client = getApiClient()
      const answer = await client.get<Record<string, unknown>>('search', {
        prompt,
        chatCompletion: 'true',
        collectionId,
      })
      setAnswers({
        prompt,
        collection: [...collection.value],
        ...answer,
      })
    } catch (error) {
      appStore.setErrorMessage({
        technicalError: error instanceof Error ? error.message : String(error),
        text: 'Error calling get answer service',
      })
    } finally {
      answersLoading.value = false
    }
  }

  async function getAnswerRag(ragVariant: Record<string, unknown>, rag: Record<string, unknown>) {
    const prompt = searchPrompt.value
    const mFilter = convertFiltersToFilterObject(metadataFilter.value)
    const col = (ragVariant?.retrieve as Record<string, unknown>)?.collection_system_names || []

    const ragPayload = { ...ragVariant, ...rag }
    delete ragPayload.variants

    answersLoading.value = true
    try {
      const client = getApiClient()
      const answer = await client.post<Record<string, unknown>>('rag_tools/test', {
        ...ragPayload,
        user_message: prompt,
        metadata_filter: mFilter,
      })
      setAnswers({
        prompt,
        collection: Array.isArray(col) ? [...col] : [],
        ...answer,
      })
    } catch (error) {
      appStore.setErrorMessage({
        technicalError: error instanceof Error ? error.message : String(error),
        text: 'Error calling get RAG answer service',
      })
    } finally {
      answersLoading.value = false
    }
  }

  async function getAnswerRagExecute(ragToolCode: string | null = null, ragSystemName?: string) {
    const prompt = searchPrompt.value

    answersLoading.value = true
    try {
      const client = getApiClient()
      const answer = await client.post<Record<string, unknown>>('rag_tools/execute', {
        user_message: prompt,
        system_name: ragToolCode || ragSystemName || 'RAG_TOOL_TEST',
      })
      setAnswers({
        prompt,
        ...answer,
      })
    } catch (error) {
      appStore.setErrorMessage({
        technicalError: error instanceof Error ? error.message : String(error),
        text: 'Error calling get answer RAG execute service',
      })
    } finally {
      answersLoading.value = false
    }
  }

  async function getAnswerRetrieval(retrievalVariant: Record<string, unknown>, rag: Record<string, unknown>) {
    const prompt = searchPrompt.value
    const col = (retrievalVariant?.retrieve as Record<string, unknown>)?.collection_system_names || []
    const mFilter = convertFiltersToFilterObject(metadataFilter.value)
    const retrieval = { ...retrievalVariant, ...rag }
    delete retrieval.variants

    answersLoading.value = true
    try {
      const client = getApiClient()
      const answer = await client.post<Record<string, unknown>>('retrieval_tools/test', {
        ...retrieval,
        user_message: prompt,
        metadata_filter: mFilter,
      })
      setAnswers({
        prompt,
        collection: Array.isArray(col) ? [...col] : [],
        ...answer,
      })
    } catch (error) {
      appStore.setErrorMessage({
        technicalError: error instanceof Error ? error.message : String(error),
        text: 'Error calling get answer retrieval service',
      })
    } finally {
      answersLoading.value = false
    }
  }

  async function getAnswerRetrievalExecute(retrievalCode: string | null = null, retrievalSystemName?: string) {
    const prompt = searchPrompt.value

    answersLoading.value = true
    try {
      const client = getApiClient()
      const answer = await client.post<Record<string, unknown>>('retrieval_tools/execute', {
        user_message: prompt,
        system_name: retrievalCode || retrievalSystemName || 'TEST_RETRIEVAL',
      })
      setAnswers({
        prompt,
        ...answer,
      })
    } catch (error) {
      appStore.setErrorMessage({
        technicalError: error instanceof Error ? error.message : String(error),
        text: 'Error calling get answer retrieval execute service',
      })
    } finally {
      answersLoading.value = false
    }
  }

  async function sendFeedback({ id, like, comment }: { id: string; like: boolean; comment: string }) {
    try {
      const client = getApiClient()
      await client.post('feedbacks', { searchId: id, like, comment })
      setFeedback({ id, like, comment })
      return true
    } catch (error) {
      appStore.setErrorMessage({
        text: 'Error sending feedback',
        technicalError: error instanceof Error ? error.message : String(error),
      })
      return false
    }
  }

  return {
    // state
    searchPrompt,
    metadataFilter,
    collectionList,
    collection,
    answersLoading,
    answers,
    feedback,
    semanticSearchAnswers,
    semanticSearchLoading,
    semanticSearch,
    // computed
    publicCollectionList,
    // actions
    clearAnswers,
    setAnswers,
    setFeedback,
    getAnswer,
    getAnswerRag,
    getAnswerRagExecute,
    getAnswerRetrieval,
    getAnswerRetrievalExecute,
    sendFeedback,
  }
})
