import { fetchData } from '@shared'

const state = () => ({
  conversation: null,
})

const getters = {
  conversation: (state) => state.conversation,
}

const mutations = {
  setConversation(state, payload) {
    state.conversation = payload
  },
}

const actions = {
  async getConversation({ commit, getters }, payload) {
    const endpoint = getters.config.api.aiBridge.urlAdmin
    try {
      const response = await fetchData({
        method: 'GET',
        endpoint,
        credentials: 'include',
        service: `agents/${payload.conversation_id}`,
      })
      const data = await response.json()
      commit('setConversation', data)
    } catch (error) {
      console.error(error)
    }
  },
}

export default {
  state,
  getters,
  mutations,
  actions,
}
