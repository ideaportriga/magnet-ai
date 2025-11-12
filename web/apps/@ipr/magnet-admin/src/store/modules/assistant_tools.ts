import _ from 'lodash'
import { fetchData } from '@shared'

// state
const state = () => ({
  assistant_tool: {
    id: '',
    name: '',
    system_name: '',
    description: '',
  },
  initialAssistantTool: null,
})

// getters
const getters = {
  assistant_tool: (state) => state.assistant_tool,
  isCancelAvailable(state, getters) {
    return !getters.assistant_tool?._metadata
  },
  isAssistantToolChanged(state) {
    if (!state.initialAssistantTool) return false
    return !_.isEqual(state.assistant_tool, state.initialAssistantTool)
  },
}

// mutations
const mutations = {
  revertAssistantToolChanges(state) {
    state.assistant_tool = _.cloneDeep(state.initialAssistantTool)
  },
  setInitAssistantTool(state, payload) {
    state.initialAssistantTool = _.cloneDeep(state.assistant_tool)
  },
  setAssistantTool(state, payload) {
    state.assistant_tool = _.cloneDeep(payload)
    state.initialAssistantTool = _.cloneDeep(payload)
  },
  updateAssistantTool(state, payload) {
    state.assistant_tool = { ...state.assistant_tool, ...payload }
  },
  updateMetadata(state, payload) {
    state.assistant_tool._metadata = { ...state.assistant_tool._metadata, ...payload }
  },
  updateAssistantToolProperty(state, { key, value }) {
    state.assistant_tool[key] = value
  },
  updateNestedAssistantToolProperty(state, { path, value }) {
    const keys = path.split('.')
    let target = state.assistant_tool
    for (let i = 0; i < keys.length - 1; i++) {
      if (!(keys[i] in target) || target[keys[i]] === null) {
        target = target[keys[i]] = {}
      } else {
        target = target[keys[i]]
      }
    }
    target[keys[keys.length - 1]] = value
  },
}

// actions
const actions = {
  async getAssistantConfigFromFile({ getters, commit, state }, payload) {
    const endpoint = getters.config?.search?.endpoint
    const formData = new FormData()

    if (payload.file) {
      formData.append('file', payload.file)
    }

    delete payload.file

    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `assistant_tools/generate-from-openapi`,
      body: formData,
      headers: {},
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((collection) => {
        return collection
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error creating collection`,
        }
      })
  },
  async getAssistantConfigFromRAG({ getters, commit, state }, payload) {
    const endpoint = getters.config?.search?.endpoint

    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `assistant_tools/generate-from-rag-tool`,
      body: payload,

      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((collection) => {
        return collection
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error creating collection`,
        }
      })
  },

  async saveAssistantTool({ commit, dispatch, getters }, payload) {
    const entity = 'assistant_tools'
    if (getters.assistant_tool?.created_at) {
      await dispatch(
        'chroma/update',
        { payload: { id: getters.assistant_tool.id, data: JSON.stringify(getters.assistant_tool) }, entity },
        { root: true }
      )
    } else {
      await dispatch('chroma/create', { payload: JSON.stringify(getters.assistant_tool), entity }, { root: true })
    }
    commit('setInitAssistantTool')
  },
  updateAssistantTool({ commit }, payload) {
    commit('updateaAssistantTool', payload)
  },
  updateMetadata({ commit }, payload) {
    commit('updateMetadata', payload)
  },
  updateAssistantToolProperty({ commit }, payload) {
    commit('updateAssistantToolProperty', payload)
  },
  updateNestedAssistantToolProperty({ commit }, payload) {
    commit('updateNestedAssistantToolProperty', payload)
  },
}

export default {
  namespaced: true,
  state: state(),
  getters,
  mutations,
  actions,
}
