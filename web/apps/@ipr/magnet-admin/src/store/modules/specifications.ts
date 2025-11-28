import _ from 'lodash'
import { fetchData } from '@shared'

// state
const state = () => ({
  specifications: [],
})

// getters
const getters = {
  specifications: (state) => state.specifications.map((val, idx) => ({ id: idx, ...val })),
}

// mutations
const mutations = {}

// actions
const actions = {
  async getSpecifications({ getters, commit }) {
    const config = {
      endpoint: getters.config?.specifications?.endpoint,
      service: getters.config?.specifications?.service,
    }
    const response = await fetchData({
      endpoint: config.endpoint,
      service: config.service,
      method: 'GET',
      headers: {
        'ngrok-skip-browser-warning': '69420',
      },
    })
    if (response?.error) {
      commit('set', {
        errorMessage: {
          technicalError: response?.error,
          text: `Error calling specifications service`,
        },
      })
      return false
    } else {
      const json = await response.json()
      commit('set', { specifications: json })
      return true
    }
  },
  async upsertSpecification({ getters, commit }, { id = '', specification }) {
    const config = {
      endpoint: getters.config?.specifications?.endpoint,
      service: getters.config?.specifications?.service,
    }
    const response = await fetchData({
      endpoint: config.endpoint,
      service: `${config.service}${id ? `/${id}` : ''}`,
      method: id ? 'PUT' : 'POST',
      headers: {
        'ngrok-skip-browser-warning': '69420',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(specification),
    })

    if (response?.error) {
      commit('set', {
        errorMessage: {
          technicalError: response?.error,
          text: `Error calling specifications service`,
        },
      })
    } else {
      const json = await response.json()
      return json
    }
  },
  async removeSpecification({ getters, commit }, { id = '' }) {
    const config = {
      endpoint: getters.config?.specifications?.endpoint,
      service: getters.config?.specifications?.service,
    }
    const response = await fetchData({
      endpoint: config.endpoint,
      service: `${config.service}/${id}`,
      method: 'DELETE',
      headers: {
        'ngrok-skip-browser-warning': '69420',
      },
    })

    if (response?.error) {
      commit('set', {
        errorMessage: {
          technicalError: response?.error,
          text: `Error calling specifications service`,
        },
      })
      return false
    } else {
      return true
    }
  },
}

export default {
  state: state(),
  getters,
  mutations,
  actions,
}
