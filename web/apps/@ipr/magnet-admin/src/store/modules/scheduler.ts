import { fetchData } from '@shared'
import _ from 'lodash'

// state
const state = () => ({})

// getters
const getters = {}

// mutations
const mutations = {}

// actions
const actions = {
  async createAndRunJobScheduler({ getters, rootGetters, commit, state }, payload) {
    const endpoint = getters.config?.scheduler?.endpoint
    const service = getters.config?.scheduler?.service
    const credentials = getters.config?.scheduler?.credentials

    commit('set', { loading: true })

    const response = await fetchData({
      method: 'POST',
      endpoint,
      service: service + '/create-job',
      credentials,
      body: JSON.stringify({
        ...payload,
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
          text: `Error calling create and run job scheduler service`,
        },
      })
    } else {
      const answer = await response.json()
      return answer
    }
  },

  async cancelJobScheduler({ getters, commit }, jobId) {
    const endpoint = getters.config?.scheduler?.endpoint
    const service = getters.config?.scheduler?.service
    const credentials = getters.config?.scheduler?.credentials

    commit('set', { loading: true })

    const response = await fetchData({
      method: 'POST',
      endpoint,
      service: service + '/cancel-job',
      credentials,
      body: JSON.stringify({
        job_id: jobId,
      }),
      headers: {
        'Content-Type': 'application/json',
      },
    })

    commit('set', { loading: false })

    if (response?.error) {
      commit('set', {
        errorMessage: {
          technicalError: response?.error,
          text: `Error canceling job`,
        },
      })
    } else {
      const answer = await response.json()
      return answer
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
