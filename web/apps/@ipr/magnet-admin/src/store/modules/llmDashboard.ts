const state = () => ({
  llmDashboardOptions: [],
})

const getters = {
  llmDashboardOptions: (state) => state.llmDashboardOptions,
}

const mutations = {
  setLlmDashboardOptions(state, options) {
    state.llmDashboardOptions = options
  },
}

const actions = {
  setLlmDashboardOptions({ commit }, options) {
    commit('setLlmDashboardOptions', options)
  },
}

export default {
  namespaced: true,
  state: state(),
  getters,
  mutations,
  actions,
}
