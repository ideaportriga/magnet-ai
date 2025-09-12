import { fetchData } from '@shared'
import _ from 'lodash'

// state
const state = () => ({
  conversation_id: null,
  agent_detail: {
    name: '',
    system_name: '',
    description: '',
    id: '',
    variants: [],
    active_variant: null,
  },
  selectedAgentDetailVariant: null,
  initialAgentDetail: null,
  agentTestSetItem: {},
  activeTopic: null,
})

// getters
const getters = {
  activeTopic: (state) => state.activeTopic,
  agentTestSetItem: (state) => state.agentTestSetItem,
  conversation_id: (state) => state.conversation_id,
  agent_detail: (state) => state.agent_detail,
  agentDetailVariant: (state) => {
    return state.agent_detail?.variants?.find((el) => el.variant === state.selectedAgentDetailVariant)
  },
  selectedAgentDetailVariant: (state) => state.selectedAgentDetailVariant,

  isAgentDetailChanged(state) {
    if (!state.initialAgentDetail) return false
    return !_.isEqual(state.agent_detail, state.initialAgentDetail)
  },

  isCancelAvailable(state, getters) {
    return !getters.agent_detail?._metadata
  },
}

// mutations
const mutations = {
  setActiveTopic(state, payload) {
    state.activeTopic = payload
  },
  setAgentTestSetItem(state, payload) {
    state.agentTestSetItem = payload
  },
  setConversationId(state, conversationId) {
    state.conversation_id = conversationId
  },
  setSelectedAgentDetailVariant(state, payload) {
    state.selectedAgentDetailVariant = payload
  },
  setInitAgentDetail(state) {
    state.initialAgentDetail = _.cloneDeep(state.agent_detail)
    state.agentTestSetItem = {}
    state.activeTopic = null
  },
  setAgentDetail(state, payload) {
    state.agent_detail = _.cloneDeep(payload)
    state.initialAgentDetail = _.cloneDeep(payload)
    state.selectedAgentDetailVariant = payload?.active_variant
    state.agentTestSetItem = {}
    state.activeTopic = null
  },
  updateAgentDetail(state, payload) {
    state.agent_detail = { ...state.agent_detail, ...payload }
  },
  updateMetadata(state, payload) {
    state.agent_detail._metadata = { ...state.agent_detail._metadata, ...payload }
  },
  updateAgentDetailProperty(state, { key, value }) {
    state.agent_detail[key] = value
  },
  updateNestedAgentDetailProperty(state, { path, value }) {
    const variant = state.agent_detail.variants.find((el) => el.variant === state.selectedAgentDetailVariant)
    if (variant) {
      const keys = path.split('.')
      let target = variant.value

      for (let i = 0; i < keys.length - 1; i++) {
        if (!(keys[i] in target) || target[keys[i]] === null) {
          target = target[keys[i]] = {}
        } else {
          target = target[keys[i]]
        }
      }

      const lastKey = keys[keys.length - 1]

      if (value === null) {
        delete target[lastKey]
      } else {
        target[lastKey] = value
      }
    }
  },

  revertAgentDetailChanges(state) {
    state.agent_detail = _.cloneDeep(state.initialAgentDetail)
  },

  createAgentDetailVariant(state, { baseVariantKey = null } = {}) {
    const baseVariant = state.agent_detail.variants.find((el) => el.variant === state.selectedAgentDetailVariant)

    const maxVariantNumber = state.agent_detail.variants.reduce((max, el) => {
      const variantNumber = parseInt(el.variant.split('_')[1]) || 0
      return Math.max(max, variantNumber)
    }, 0)
    const newVariantKey = `variant_${maxVariantNumber + 1}`

    const newVariant = baseVariant ? { ..._.cloneDeep(baseVariant), variant: newVariantKey, description: '' } : { variant: newVariantKey }

    state.agent_detail.variants.push(newVariant)

    state.selectedAgentDetailVariant = newVariantKey
  },
  deleteAgentDetailVariant(state) {
    if (state.agent_detail.variants.length > 1) {
      const index = state.agent_detail.variants.findIndex((el) => el.variant === state.selectedAgentDetailVariant)

      if (index !== -1) {
        const isActiveVariant = state.selectedAgentDetailVariant === state.agent_detail.active_variant

        state.agent_detail.variants.splice(index, 1)

        const newIndex = index === 0 ? 0 : index - 1
        state.selectedAgentDetailVariant = state.agent_detail.variants[newIndex].variant

        if (isActiveVariant) {
          state.agent_detail.active_variant = state.selectedAgentDetailVariant
        }
      }
    }
  },
  activateAgentDetailVariant(state) {
    state.agent_detail.active_variant = state.selectedAgentDetailVariant
  },
  updateNestedAgentDetailListItemBySystemName(state, { arrayPath, itemSystemName, subArrayKey, subItemSystemName, data }) {
    const variant = state.agent_detail.variants.find((el) => el.variant === state.selectedAgentDetailVariant)
    if (!variant) return

    const itemsArray = _.get(variant.value, arrayPath)
    if (!Array.isArray(itemsArray)) return

    const item = itemsArray.find((el) => el.system_name === itemSystemName)
    if (!item) return

    if (subArrayKey) {
      const subItemsArray = item[subArrayKey]
      if (!Array.isArray(subItemsArray)) return

      const subItem = subItemsArray.find((el) => el.system_name === subItemSystemName)
      if (!subItem) return

      Object.assign(item, { metadata: { ...item.metadata, modified_at: new Date().toISOString() } })
      Object.assign(subItem, { ...data, metadata: { ...subItem.metadata, modified_at: new Date().toISOString() } })
    } else {
      Object.assign(item, { ...data, metadata: { ...item.metadata, modified_at: new Date().toISOString() } })
    }
  },
}

// actions
const actions = {
  async testAgent({ getters, rootGetters, commit, state }, { trace_id, ...payload }) {
    const endpoint = getters.config?.agent?.endpoint
    const service = `${getters.config?.agent?.service}` || ''
    const credentials = getters.config?.agent?.credentials

    commit('set', { answersLoading: true })

    const response = await fetchData({
      method: 'POST',
      endpoint,
      service: service + '/test' + (trace_id ? '?trace_id=' + trace_id : ''),
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
          text: `Error calling test agent service`,
        },
      })
    } else {
      const answer = await response.json()
      return answer
    }
  },
  async executeAgent({ getters, rootGetters, commit, state }, { trace_id, ...payload }) {
    const endpoint = getters.config?.agent?.endpoint
    const service = `${getters.config?.agent?.service}` || ''
    const credentials = getters.config?.agent?.credentials

    commit('set', { answersLoading: true })

    const response = await fetchData({
      method: 'POST',
      endpoint,
      service: service + '/execute' + (trace_id ? '?trace_id=' + trace_id : ''),
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
          text: `Error calling execute agent service`,
        },
      })
    } else {
      const answer = await response.json()
      return answer
    }
  },
  async createConversation({ getters, rootGetters, commit, state }, { agent, user_message_content, client_id }) {
    const config = getters.config?.agent_conversations
    const endpoint = config?.endpoint
    const service = `${config?.service}` || ''
    const credentials = config?.credentials

    commit('set', { answersLoading: true })
    const response = await fetchData({
      method: 'POST',
      endpoint,
      service: service,
      credentials,
      body: JSON.stringify({
        agent,
        user_message_content,
        client_id,
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
          text: `Error calling create conversation service`,
        },
      })
    } else {
      const answer = await response.json()
      return answer
    }
  },
  async addUserMessageToConversation({ getters, rootGetters, commit, state }, { conversation_id, user_message_content }) {
    const config = getters.config?.agent_conversations
    const endpoint = config?.endpoint
    const service = `${config?.service}` || ''
    const credentials = config?.credentials
    

    commit('set', { answersLoading: true })

    const response = await fetchData({
      method: 'POST',
      endpoint,
      service: `${service}/${conversation_id}/messages`,
      credentials,
      body: JSON.stringify({
        user_message_content,
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
          text: `Error calling new conversation message service`,
        },
      })
    } else {
      const answer = await response.json()
      return answer
    }
  },
  async getConversation({ getters, rootGetters, commit, state }, { conversation_id }) {
    const config = getters.config?.agent_conversations
    const endpoint = config?.endpoint
    const service = `${config?.service}` || ''
    const credentials = config?.credentials

    commit('set', { answersLoading: true })

    const response = await fetchData({
      method: 'GET',
      endpoint,
      service: `${service}/${conversation_id}`,
      credentials,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    commit('set', { answersLoading: false })

    if (response?.error) {
      commit('set', {
        errorMessage: {
          technicalError: response?.error,
          text: `Error calling get conversation service`,
        },
      })
    } else {
      const answer = await response.json()
      return answer
    }
  },
  async getLastRelevantConversation({ getters, rootGetters, commit, state }, { client_id }) {
    const config = getters.config?.agent_conversations
    const endpoint = config?.endpoint
    const service = `${config?.service}` || ''
    const credentials = config?.credentials

    commit('set', { answersLoading: true })

    const encodedClientId = encodeURIComponent(client_id)
    const response = await fetchData({
      method: 'GET',
      endpoint,
      service: `${service}/client/${encodedClientId}`,
      credentials,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    commit('set', { answersLoading: false })

    if (response?.error) {
      commit('set', {
        errorMessage: {
          technicalError: response?.error,
          text: `123 Error calling last relevant conversation service`,
        },
      })
    } else {
      const answer = await response.json()
      return answer
    }
  },
  async saveAgentDetail({ commit, dispatch, getters }, payload) {
    const entity = 'agents'
    const obj = { ...getters.agent_detail }
    delete obj._metadata
    delete obj.id

    if (getters.agent_detail?.created_at) {
      await dispatch('chroma/update', { payload: { id: getters.agent_detail.id, data: obj }, entity }, { root: true })
    } else {
      await dispatch('chroma/create', { payload: obj, entity }, { root: true })
    }
    commit('setInitAgentDetail')
  },
  updateAgentDetail({ commit }, payload) {
    commit('updateAgentDetail', payload)
  },
  updateMetadata({ commit }, payload) {
    commit('updateMetadata', payload)
  },
  updateAgentDetailProperty({ commit }, payload) {
    commit('updateAgentDetailProperty', payload)
  },
  updateNestedAgentDetailProperty({ commit }, payload) {
    commit('updateNestedAgentDetailProperty', payload)
  },
  updateConversationId({ commit }, conversationId) {
    commit('setConversationId', conversationId)
  },
  async postProcessConversation({ getters, commit }, { conversation_id }) {
    const config = getters.config?.agent
    const endpoint = config?.endpoint
    const service = `${config?.service}` || ''
    const credentials = config?.credentials

    commit('set', { answersLoading: true })
    const response = await fetchData({
      method: 'POST',
      endpoint,
      service: `${service}/post_process_conversation?conversation_id=${encodeURIComponent(conversation_id)}`,
      credentials,
    })
    commit('set', { answersLoading: false })

    if (response?.error) {
      commit('set', {
        errorMessage: {
          technicalError: response.error,
          text: `Error calling post process conversation service`,
        },
      })
    } else {
      const result = await response.json()
      return result
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
