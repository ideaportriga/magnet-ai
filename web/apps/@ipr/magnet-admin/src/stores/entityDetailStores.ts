/**
 * Supplementary Pinia stores for entity detail pages.
 *
 * NOTE: The entity detail stores (useProviderDetailStore, useRagDetailStore, etc.)
 * have been migrated to composables (useEntityDetail, useVariantEntityDetail, useAgentEntityDetail).
 * Only supplementary stores remain here.
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { createEntityDetailStore } from './entityDetailStoreFactory'

// Legacy: still used by Collections/FileUrlUpload.vue in CreateNew context (no route ID)
// TODO: Remove when FileUrlUpload is refactored to use props/emit for creation flow
export const useCollectionDetailStore = createEntityDetailStore('collection')

// Collection metadata config store (supplements collection detail)
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

// Evaluation set record store (supplements evaluation set detail)
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
