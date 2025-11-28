const state = () => ({
  ragDashboardOptions: [],
})

const getters = {
  ragDashboardOptions: (state) => state.ragDashboardOptions,
}

const mutations = {
  setRagDashboardOptions(state, options) {
    state.ragDashboardOptions = options
  },
}

const actions = {
  setRagDashboardOptions({ commit }, options) {
    commit('setRagDashboardOptions', options)
  },
}

export default {
  namespaced: true,
  state: state(),
  getters,
  mutations,
  actions,
}
