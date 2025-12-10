// store/modules/knowledgeGraph.ts
// Manages Knowledge Graph page state, particularly unsaved changes tracking for Retrieval tab

interface KnowledgeGraphState {
  isRetrievalChanged: boolean
  pendingSaveCallback: (() => Promise<void>) | null
  pendingRevertCallback: (() => void) | null
}

export default {
  state: {
    isRetrievalChanged: false,
    pendingSaveCallback: null,
    pendingRevertCallback: null,
  } as KnowledgeGraphState,

  getters: {
    isKnowledgeGraphRetrievalChanged: (state: KnowledgeGraphState) => state.isRetrievalChanged,
    knowledgeGraphPendingSave: (state: KnowledgeGraphState) => state.pendingSaveCallback,
    knowledgeGraphPendingRevert: (state: KnowledgeGraphState) => state.pendingRevertCallback,
  },

  mutations: {
    setKnowledgeGraphRetrievalChanged(state: KnowledgeGraphState, changed: boolean) {
      state.isRetrievalChanged = changed
    },
    setKnowledgeGraphSaveCallback(state: KnowledgeGraphState, callback: (() => Promise<void>) | null) {
      state.pendingSaveCallback = callback
    },
    setKnowledgeGraphRevertCallback(state: KnowledgeGraphState, callback: (() => void) | null) {
      state.pendingRevertCallback = callback
    },
    clearKnowledgeGraphCallbacks(state: KnowledgeGraphState) {
      state.pendingSaveCallback = null
      state.pendingRevertCallback = null
    },
    revertKnowledgeGraphChanges(state: KnowledgeGraphState) {
      if (state.pendingRevertCallback) {
        state.pendingRevertCallback()
      }
      state.isRetrievalChanged = false
    },
  },

  actions: {
    async saveKnowledgeGraph({ state, commit }: { state: KnowledgeGraphState; commit: Function }) {
      if (state.pendingSaveCallback) {
        await state.pendingSaveCallback()
      }
      commit('setKnowledgeGraphRetrievalChanged', false)
    },
  },
}

