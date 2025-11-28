// state
const state = () => ({
  trace: {},
})

// getters
const getters = {
  // fix
  trace: (state, getters, rootState, rootGetters) => rootGetters['chroma'].observability_traces.selectedRow,

  isCancelAvailable(state, getters) {
    return !getters.trace?._metadata
  },
}

// mutations
const mutations = {
  setTrace(state, payload) {
    state.trace = payload
  },
}

export default {
  namespaced: true,
  state: state(),
  getters,
  mutations,
}
