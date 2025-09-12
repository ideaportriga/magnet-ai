import _ from 'lodash'
import { fetchData } from '@shared'

// state
const state = () => ({
  searchPrompt: '',
  collectionList: [],
  collection: [],
  answersLoading: false,
  answers: [],
  feedback: {},
})

// getters
const getters = {
  searchPrompt: (state) => state.searchPrompt,
  collectionList: (state) => state.collectionList,
  publicCollectionList: (state) => {
    return (
      state.collectionList
        ?.map(({ id, name, show_in_qa }) => ({ id, value: name, label: name, show_in_qa }))
        ?.filter(({ show_in_qa }) => show_in_qa) || []
    )
  },
  collection: (state) => state.collection,
  answersLoading: (state) => state.answersLoading,
  answers: (state) => state.answers,
  feedback: (state) => state.feedback,
}

// mutations
const mutations = {
  clearAnswers(state) {
    state.answers = []
  },
  setAnswers(state, answer) {
    state.answers = [answer, ...state.answers]
  },

  setFeedback(state, { id, like, comment }) {
    const answerIndex = state.answers.findIndex((answer) => {
      return answer.id === id
    })
    state.answers[answerIndex].feedback = { like, comment }
  },
}

// actions
const actions = {
  async getAnswer({ getters, rootGetters, commit, state }) {
    const prompt = state.searchPrompt
    const collection = getters.chroma?.collections?.publicSelected
    const endpoint = getters.config?.search?.endpoint
    const service = getters.config?.search?.service || ''
    const credentials = getters.config?.search?.credentials
    commit('set', { answersLoading: true })
    const response = await fetchData({
      endpoint,
      service,
      credentials,
      queryParams: {
        prompt: prompt,
        chatCompletion: 'true',
        collectionId: collection.map((value) => value).join(',') || 'default_collection',
      },
    })

    commit('set', { answersLoading: false })

    if (response?.error) {
      commit('set', {
        errorMessage: {
          technicalError: response?.error,
          text: `Error calling get answer service`,
        },
      })
    } else {
      const answer = await response.json()
      commit('setAnswers', {
        prompt,
        collection: [...collection],
        ...answer,
      })
    }
  },
  async getAnswerRag({ getters, rootGetters, commit, state }) {
    const prompt = state.searchPrompt
    const collection = getters.ragVariant?.retrieve?.collection_system_names || {}
    const endpoint = getters.config?.rag?.endpoint
    const service = `${getters.config?.rag?.service}` || ''
    const credentials = getters.config?.rag?.credentials

    const rag = { ...getters.ragVariant, ...getters.rag }
    delete rag.variants

    commit('set', { answersLoading: true })
    const response = await fetchData({
      method: 'POST',
      endpoint,
      service: service + '/test',
      credentials,
      body: JSON.stringify({
        ...rag,
        user_message: prompt,
      }),
      headers: {
        'Content-Type': 'application/json',
      },
    })

    commit('set', { answersLoading: false })

    if (response?.error) {
      commit('set', {
        errorMessage: {
          technicalError: response?.error,
          text: `Error calling get RAG answer service`,
        },
      })
    } else {
      const answer = await response.json()
      commit('setAnswers', {
        prompt,
        collection: [...collection],
        ...answer,
      })
    }
  },
  async getAnswerRagExecute({ getters, rootGetters, commit, state }, ragToolCode = null) {
    const prompt = state.searchPrompt
    const endpoint = getters.config?.rag?.endpoint
    const service = getters.config?.rag?.service || ''
    const credentials = getters.config?.rag?.credentials
    const ragToolCodeDefault = getters.rag?.system_name
    commit('set', { answersLoading: true })
    const response = await fetchData({
      method: 'POST',
      endpoint,
      service: service + '/execute',
      credentials,
      body: JSON.stringify({
        user_message: prompt,
        system_name: ragToolCode || ragToolCodeDefault || 'RAG_TOOL_TEST',
      }),
      headers: {
        'Content-Type': 'application/json',
      },
    })

    commit('set', { answersLoading: false })

    if (response?.error) {
      commit('set', {
        errorMessage: {
          technicalError: response?.error,
          text: `Error calling get answer RAG execute service`,
        },
      })
    } else {
      const answer = await response.json()
      commit('setAnswers', {
        prompt,
        ...answer,
      })
    }
  },
  async getAnswerRetrieval({ getters, rootGetters, commit, state }) {
    const prompt = state.searchPrompt
    const collection = getters.retrievalVariant?.retrieve?.collection_system_names || {}
    const endpoint = getters.config?.retrieval?.endpoint
    const service = `${getters.config?.retrieval?.service}` || ''
    const credentials = getters.config?.retrieval?.credentials
    const retrieval = { ...getters.retrievalVariant, ...getters.rag }
    delete retrieval.variants

    commit('set', { answersLoading: true })
    const response = await fetchData({
      method: 'POST',
      endpoint,
      service: service + '/test',
      credentials,
      body: JSON.stringify({
        ...retrieval,
        user_message: prompt,
      }),
      headers: {
        'Content-Type': 'application/json',
      },
    })

    commit('set', { answersLoading: false })

    if (response?.error) {
      commit('set', {
        errorMessage: {
          technicalError: response?.error,
          text: `Error calling get answer retrieval service`,
        },
      })
    } else {
      const answer = await response.json()
      
      commit('setAnswers', {
        prompt,
        collection: [...collection],
        ...answer,
      })
    }
  },
  async getAnswerRetrievalExecute({ getters, rootGetters, commit, state }, retrievalCode = null) {
    const prompt = state.searchPrompt
    const endpoint = getters.config?.retrieval?.endpoint
    const service = getters.config?.retrieval?.service || ''
    const credentials = getters.config?.retrieval?.credentials
    const retrievalToolCodeDefault = getters.retrieval?.system_name
    commit('set', { answersLoading: true })
    const response = await fetchData({
      method: 'POST',
      endpoint,
      service: service + '/execute',
      credentials,
      body: JSON.stringify({
        user_message: prompt,
        system_name: retrievalCode || retrievalToolCodeDefault || 'TEST_RETRIEVAL',
      }),
      headers: {
        'Content-Type': 'application/json',
      },
    })

    commit('set', { answersLoading: false })

    if (response?.error) {
      commit('set', {
        errorMessage: {
          technicalError: response?.error,
          text: `Error calling get answer retrieval execute service`,
        },
      })
    } else {
      const answer = await response.json()
      commit('setAnswers', {
        prompt,
        ...answer,
      })
    }
  },
  async sendFeedback({ getters, commit, state }, { id, like, comment }) {
    const endpoint = getters.config?.feedbacks?.endpoint
    const service = getters.config?.feedbacks?.service || ''
    let responseStatus = false

    const response = await fetchData({
      endpoint,
      service,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ searchId: id, like, comment }),
      credentials: 'include',
    })

    const result = await response?.text()

    console.debug({ id, like, comment }, result)

    if (result !== 'Created') {
      commit('set', {
        errorMessage: {
          text: `Error sending feedback`,
        },
        // errorMessage: {
        //   technicalError: response?.error ?? response,
        //   text: `Error sending feedback`
        // }
      })
    } else {
      responseStatus = true
      commit('setFeedback', { id, like, comment })
    }

    return responseStatus
  },
}

export default {
  state: state(),
  getters,
  mutations,
  actions,
}
