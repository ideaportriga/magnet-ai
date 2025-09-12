import _ from 'lodash'
// state
const state = () => ({
  retrieval: {
    name: '',
    system_name: '',
    description: '',
    id: '',
    variants: [],
    active_variant: '',
  },
  selectedRetrievalVariant: null,
  initialRetrieval: null,
  retrievalTestSetItem: {},

})

// getters
const getters = {
  retrieval: (state) => state.retrieval,
  retrievalVariant: (state) => {
    return state.retrieval.variants?.find((el) => el.variant === state.selectedRetrievalVariant)
  },
  selectedRetrievalVariant: (state) => state.selectedRetrievalVariant,
  isCancelAvailable(state, getters) {
    return !getters.retrieval?._metadata
  },
  isRetrievalChanged(state) {
    if (!state.initialRetrieval) return false
    return !_.isEqual(state.retrieval, state.initialRetrieval)
  },

  retrievalTestSetItem: (state) => state.retrievalTestSetItem,
}

// mutations
const mutations = {
  setRetrievalTestSetItem(state, payload) {
    state.retrievalTestSetItem = payload
  },
  setSelectedRetrievalVariant(state, payload) {
    console.log('setSelectedRetrievalVariant', payload)
    state.selectedRetrievalVariant = payload
  },
  revertRetrievalChanges(state) {
    state.retrieval = _.cloneDeep(state.initialRetrieval)
  },
  setInitRetrieval(state, payload) {
    state.initialRetrieval = _.cloneDeep(state.retrieval)
  },
  setRetrieval(state, payload) {
    console.log('setRetrieval', payload)
    state.retrieval = _.cloneDeep(payload)
    state.initialRetrieval = _.cloneDeep(payload)
    state.selectedRetrievalVariant = payload?.active_variant
    console.log(state.selectedRetrievalVariant)
  },
  updateRetrieval(state, payload) {
    state.retrieval = { ...state.retrieval, ...payload }
  },
  updateMetadata(state, payload) {
    state.retrieval._metadata = { ...state.retrieval._metadata, ...payload }
  },
  updateRetrievalProperty(state, { key, value }) {
    state.retrieval[key] = value
  },
  updateNestedRetrievalProperty(state, { path, value }) {
    const variant = state.retrieval.variants.find((el) => el.variant === state.selectedRetrievalVariant)
    if (variant) {
      const keys = path.split('.')
      let target = variant

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
  createRetrievalVariant(state, { baseVariantKey = null } = {}) {
    const baseVariant = state.retrieval.variants.find((el) => el.variant === state.selectedRetrievalVariant)

    const maxVariantNumber = state.retrieval.variants.reduce((max, el) => {
      const variantNumber = parseInt(el.variant.split('_')[1]) || 0
      return Math.max(max, variantNumber)
    }, 0)
    const newVariantKey = `variant_${maxVariantNumber + 1}`

    const newVariant = baseVariant ? { ..._.cloneDeep(baseVariant), variant: newVariantKey, description: '' } : { variant: newVariantKey }

    state.retrieval.variants.push(newVariant)

    state.selectedRetrievalVariant = newVariantKey
  },
  deleteRetrievalVariant(state) {
    if (state.retrieval.variants.length > 1) {
      const index = state.retrieval.variants.findIndex((el) => el.variant === state.selectedRetrievalVariant)

      if (index !== -1) {
        const isActiveVariant = state.selectedRetrievalVariant === state.retrieval.active_variant

        state.retrieval.variants.splice(index, 1)

        const newIndex = index === 0 ? 0 : index - 1
        state.selectedRetrievalVariant = state.retrieval.variants[newIndex].variant

        if (isActiveVariant) {
          state.retrieval.active_variant = state.selectedRetrievalVariant
        }
      }
    }
  },
  activateRetrievalVariant(state) {
    state.retrieval.active_variant = state.selectedRetrievalVariant
  },
}

// actions
const actions = {
  async saveRetrieval({ commit, dispatch, getters }, payload) {
    const entity = 'retrieval'
    if (getters.retrieval?.created_at) {
      await dispatch('chroma/update', { payload: { id: getters.retrieval.id, data: JSON.stringify(getters.retrieval) }, entity }, { root: true })
    } else {
      await dispatch('chroma/create', { payload: JSON.stringify(getters.retrieval), entity }, { root: true })
    }
    commit('setInitRetrieval')
  },
  updateRetrieval({ commit }, payload) {
    commit('updateretrieval', payload)
  },
  updateMetadata({ commit }, payload) {
    commit('updateMetadata', payload)
  },
  updateRetrievalProperty({ commit }, payload) {
    commit('updateRetrievalProperty', payload)
  },
  updateNestedRetrievalProperty({ commit }, payload) {
    commit('updateNestedRetrievalProperty', payload)
  },
}

export default {
  namespaced: true,
  state: state(),
  getters,
  mutations,
  actions,
}
