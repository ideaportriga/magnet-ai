import _ from 'lodash'

// state
const state = () => ({
  evaluation_set: {
    name: '',
    system_name: '',
    description: '',
    type: '',
    items: [],
  },
  evaluation_set_record: {},
  initEvaluationSet: null,
})

// getters
const getters = {
  evaluation_set: (state) => state.evaluation_set,
  evaluation_set_record: (state) => state.evaluation_set_record,
  isCancelAvailable(state, getters) {
    return !getters.evaluation_set?._metadata
  },
  isEvaluationSetChanged(state) {
    if (!state.initEvaluationSet) return false
    return !_.isEqual(state.evaluation_set, state.initEvaluationSet)
  },
}

// mutations
const mutations = {
  setInitEvaluationSet(state, payload) {
    state.initEvaluationSet = _.cloneDeep(state.evaluation_set)
  },
  setEvaluationSetRecord(state, payload) {
    state.evaluation_set_record = payload
  },
  setEvaluationSet(state, payload) {
    state.evaluation_set = payload
    state.evaluation_set_record = {}
    state.initEvaluationSet = _.cloneDeep(payload)
  },
  updateEvaluationSet(state, payload) {
    state.evaluation_set = { ...state.evaluation_set, ...payload }
  },
  updateMetadata(state, payload) {
    state.evaluation_set._metadata = { ...state.evaluation_set._metadata, ...payload }
  },
  updateEvaluationSetProperty(state, { key, value }) {
    state.evaluation_set[key] = value
  },
  updateNestedEvaluationSetProperty(state, { path, value }) {
    const keys = path.split('.')
    let target = state.evaluation_set
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
  saveEvaluationSet({ commit, dispatch, getters }, payload) {
    const entity = 'evaluation_sets'
    if (getters.evaluation_set?.created_at) {
      const obj = { ...getters.evaluation_set }
      delete obj._metadata
      delete obj.id
      dispatch('chroma/update', { payload: { id: getters.evaluation_set.id, data: obj }, entity }, { root: true })
    } else {
      dispatch('chroma/create', { payload: getters.evaluation_set, entity }, { root: true })
    }
    commit('setInitEvaluationSet')
  },

  updateEvaluationSet({ commit }, payload) {
    commit('updateEvaluationSet', payload)
  },
  updateMetadata({ commit }, payload) {
    commit('updateMetadata', payload)
  },
  updateEvaluationSetProperty({ commit }, payload) {
    commit('updateEvaluationSetProperty', payload)
  },
  updateNestedEvaluationSetProperty({ commit }, payload) {
    commit('updateNestedEvaluationSetProperty', payload)
  },
}

export default {
  namespaced: true,
  state: state(),
  getters,
  mutations,
  actions,
}
