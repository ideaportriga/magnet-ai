const state = () => ({
  agentDashboardOptions: [],
})

const getters = {
  agentDashboardOptions: (state) => state.agentDashboardOptions,
}

const mutations = {
  setAgentDashboardOptions(state, options) {
    state.agentDashboardOptions = options
  },
}

const actions = {
  setAgentDashboardOptions({ commit }, options) {
    commit('setAgentDashboardOptions', options)
  },
}

export default {
  namespaced: true,
  state: state(),
  getters,
  mutations,
  actions,
}
