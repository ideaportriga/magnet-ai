/**
 * Pinia entity detail stores.
 *
 * Each store manages form editing state for a single entity type.
 * Under the hood, mutations sync to editBufferStore for dirty tracking
 * and workspace tab dirty indicators.
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { createEntityDetailStore, createVariantDetailStore } from './entityDetailStoreFactory'

// Simple entity detail stores (no variant system)
export const useProviderDetailStore = createEntityDetailStore('provider')
export const useAiAppDetailStore = createEntityDetailStore('aiApp')
export const useCollectionDetailStore = createEntityDetailStore('collection')
export const useEvaluationSetDetailStore = createEntityDetailStore('evaluationSet')
export const useAssistantToolDetailStore = createEntityDetailStore('assistantTool')
export const useModelConfigDetailStore = createEntityDetailStore('modelConfig')
export const useMcpServerDetailStore = createEntityDetailStore('mcpServer')
export const useApiServerDetailStore = createEntityDetailStore('apiServer')
export const useApiToolDetailStore = createEntityDetailStore('apiTool')
export const useTraceDetailStore = createEntityDetailStore('trace')

// Variant-aware entity detail stores (rag, retrieval, prompts)
// Note: agents use a dedicated store in agentDetailStore.ts (has agent-specific methods)
export const useRagDetailStore = createVariantDetailStore('rag')
export const useRetrievalDetailStore = createVariantDetailStore('retrieval')
export const usePromptTemplateDetailStore = createVariantDetailStore('promptTemplate')

// Collection metadata config store (supplements useCollectionDetailStore)
export const useCollectionMetadataStore = defineStore('collectionMetadata', () => {
  const activeMetadataConfig = ref<Record<string, any> | null>(null)

  function setActiveMetadataConfig(config: Record<string, any> | null) {
    activeMetadataConfig.value = config
  }

  return {
    activeMetadataConfig,
    setActiveMetadataConfig,
  }
})

// Evaluation set record store (supplements useEvaluationSetDetailStore)
// Replaces: store.getters.evaluation_set_record / store.commit('setEvaluationSetRecord', value)
export const useEvaluationSetRecordStore = defineStore('evaluationSetRecord', () => {
  const record = ref<Record<string, any>>({})

  function setRecord(value: Record<string, any>) {
    record.value = value
  }

  return { record, setRecord }
})

/**
 * Knowledge Graph page state store.
 *
 * Coordinates save/revert between LayoutDefault (toolbar buttons) and RetrievalTab
 * (owns the actual data). RetrievalTab registers callbacks on mount and clears them
 * on unmount; LayoutDefault invokes save/revert via this store.
 *
 * TODO: Consider replacing callback refs with provide/inject or an event bus
 * when this area is refactored — storing functions in Pinia is not serializable.
 */
export const useKnowledgeGraphPageStore = defineStore('knowledgeGraphPage', () => {
  type SaveCallback = () => Promise<void>
  type RevertCallback = () => void

  const isRetrievalChanged = ref(false)
  const pendingSaveCallback = ref<SaveCallback | null>(null)
  const pendingRevertCallback = ref<RevertCallback | null>(null)

  function setRetrievalChanged(changed: boolean) {
    isRetrievalChanged.value = changed
  }

  function setSaveCallback(callback: SaveCallback | null) {
    pendingSaveCallback.value = callback
  }

  function setRevertCallback(callback: RevertCallback | null) {
    pendingRevertCallback.value = callback
  }

  function clearCallbacks() {
    pendingSaveCallback.value = null
    pendingRevertCallback.value = null
  }

  async function saveKnowledgeGraph() {
    if (pendingSaveCallback.value) {
      await pendingSaveCallback.value()
    }
    isRetrievalChanged.value = false
  }

  function revertChanges() {
    if (pendingRevertCallback.value) {
      pendingRevertCallback.value()
    }
    isRetrievalChanged.value = false
  }

  return {
    isRetrievalChanged,
    pendingSaveCallback,
    pendingRevertCallback,
    setRetrievalChanged,
    setSaveCallback,
    setRevertCallback,
    clearCallbacks,
    saveKnowledgeGraph,
    revertChanges,
  }
})
