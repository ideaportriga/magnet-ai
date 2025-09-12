import { isEqual, merge } from 'lodash'
import { fetchData } from '@shared'

// state
const state = () => ({
  knowledge: {
    name: '',
    system_name: '',
    description: '',
  },
  semanticSearch: '',
  semanticSearchAnswers: [],
  semanticSearchLoading: false,
  deleteAllLoading: false,
})

// getters
const getters = {
  deleteAllLoading: (state) => state.deleteAllLoading,
  knowledge: (state) => state.knowledge,
  isKnowledgeChanged: (state, getters, rootState, rootGetters) => {
    const dbObject = rootGetters['chroma/collections']?.items.find((el) => el.id == state.knowledge.id)
    const currentObject = state.knowledge
    const result = isEqual(dbObject, currentObject)
    return result
  },
  isCancelAvailable(state, getters) {
    return !getters.knowledge?._metadata
  },
  semanticSearchAnswers: (state) => state.semanticSearchAnswers,
  semanticSearch: (state) => state.semanticSearch,
  semanticSearchLoading: (state) => state.semanticSearchLoading,
}

// mutations
const mutations = {
  setKnowledge(state, payload) {
    state.knowledge = payload
  },
  updateKnowledge(state, payload) {
    state.knowledge = merge({}, state.knowledge, payload)
  },
  clearSemanticSeacrhAnswers(state) {
    state.semanticSearchAnswers = []
  },
  setSemanticSeacrhAnswers(state, answer) {
    state.semanticSearchAnswers = [answer, ...state.semanticSearchAnswers]
  },
}

// actions
const actions = {
  updateKnowledge({ commit }, payload) {
    commit('updateKnowledge', payload)
  },
  async getSemanticSearchAnswer({ getters, rootGetters, commit, state }) {
    const prompt = state.semanticSearch
    const collection_id = getters.knowledge?.system_name
    const endpoint = getters.config?.documentSemanticSearch?.endpoint
    const service = `${getters.config?.documentSemanticSearch?.service}` || ''
    const credentials = getters.config?.documentSemanticSearch?.credentials
    // const rag = getters.rag

    commit('set', { semanticSearchLoading: true })
    const response = await fetchData({
      method: 'POST',
      endpoint,
      service: service,
      credentials,
      body: JSON.stringify({
        collection_id,
        user_message: prompt,
      }),
      headers: {
        'Content-Type': 'application/json',
      },
    })

    commit('set', { semanticSearchLoading: false })

    if (response?.error) {
      commit('set', {
        errorMessage: {
          technicalError: response?.error,
          text: `Error calling semantic search service`,
        },
      })
    } else {
      const answer = await response.json()
      commit('setSemanticSeacrhAnswers', {
        prompt,
        collection: collection_id,
        ...answer,
      })
    }
  },
  async deleteAllDocuments({ getters, commit }, collection_id) {
    const endpoint = getters.config?.collections?.endpoint
    const serviceBase = getters.config?.collections?.service
    const service = `${serviceBase}/${collection_id}/documents/all`
    const credentials = getters.config?.collections?.credentials

    commit('set', { deleteAllLoading: true })
    const response = await fetchData({
      method: 'DELETE',
      endpoint,
      service,
      credentials,
      headers: {
        'Content-Type': 'application/json',
      },
    })
    commit('set', { deleteAllLoading: false })

    if (response?.error) {
      commit('set', {
        errorMessage: {
          technicalError: response?.error,
          text: `Error deleting documents for collection ${collection_id}`,
        },
      })
    } else {
      // Optionally handle successful deletion
      // ...existing code...
    }
  },
}

export default {
  namespaced: true,
  state: state(),
  getters,
  mutations,
  actions,
}
