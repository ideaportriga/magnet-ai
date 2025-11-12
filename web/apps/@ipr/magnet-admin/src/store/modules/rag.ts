import _ from 'lodash'

// state
const state = () => ({
  rag: {
    name: '',
    system_name: '',
    description: '',
    id: '',
    variants: [],
    active_variant: null,
  },
  selectedRagVariant: null,
  initialRag: null,
  ragTestSetItem: {},
})

// getters
const getters = {

  rag: (state) => state.rag,
  ragVariant: (state) => {
    return state.rag.variants?.find((el) => el.variant === state.selectedRagVariant)
  },
  selectedRagVariant: (state) => state.selectedRagVariant,

  isRagChanged(state) {
    if (!state.initialRag) return false
    return !_.isEqual(state.rag, state.initialRag)
  },

  isCancelAvailable(state, getters) {
    return !getters.rag?._metadata
  },
  ragTestSetItem: (state) => state.ragTestSetItem,
}

// mutations
const mutations = {
  setRagTestSetItem(state, payload) {
    state.ragTestSetItem = payload
  },
  setSelectedRagVariant(state, payload) {
    state.selectedRagVariant = payload
  },
  setInitRag(state) {
    state.initialRag = _.cloneDeep(state.rag)
  },
  setRag(state, payload) {
    state.rag = _.cloneDeep(payload)
    state.initialRag = _.cloneDeep(payload)
    state.selectedRagVariant = payload?.active_variant
  },
  updateRag(state, payload) {
    state.rag = { ...state.rag, ...payload }
  },
  updateMetadata(state, payload) {
    state.rag._metadata = { ...state.rag._metadata, ...payload }
  },
  updateRagProperty(state, { key, value }) {
    state.rag[key] = value
  },
  updateNestedRagProperty(state, { path, value }) {
    const variant = state.rag.variants.find((el) => el.variant === state.selectedRagVariant)
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

  revertRagChanges(state) {
    state.rag = _.cloneDeep(state.initialRag)
  },

  createRagVariant(state, { baseVariantKey = null } = {}) {
    const baseVariant = state.rag.variants.find((el) => el.variant === state.selectedRagVariant)

    const maxVariantNumber = state.rag.variants.reduce((max, el) => {
      const variantNumber = parseInt(el.variant.split('_')[1]) || 0
      return Math.max(max, variantNumber)
    }, 0)
    const newVariantKey = `variant_${maxVariantNumber + 1}`

    const newVariant = baseVariant ? { ..._.cloneDeep(baseVariant), variant: newVariantKey, description: '' } : { variant: newVariantKey }

    state.rag.variants.push(newVariant)

    state.selectedRagVariant = newVariantKey
  },
  deleteRagVariant(state) {
    if (state.rag.variants.length > 1) {
      const index = state.rag.variants.findIndex((el) => el.variant === state.selectedRagVariant)

      if (index !== -1) {
        const isActiveVariant = state.selectedRagVariant === state.rag.active_variant

        state.rag.variants.splice(index, 1)

        const newIndex = index === 0 ? 0 : index - 1
        state.selectedRagVariant = state.rag.variants[newIndex].variant

        if (isActiveVariant) {
          state.rag.active_variant = state.selectedRagVariant
        }
      }
    }
  },
  activateRagVariant(state) {
    state.rag.active_variant = state.selectedRagVariant
  },
}

// actions
const actions = {
  async saveRag({ commit, dispatch, getters }, payload) {
    const entity = 'rag_tools'
    if (getters.rag?.created_at) {
      await dispatch('chroma/update', { payload: { id: getters.rag.id, data: JSON.stringify(getters.rag) }, entity }, { root: true })
    } else {
      await dispatch('chroma/create', { payload: JSON.stringify(getters.rag), entity }, { root: true })
    }
    commit('setInitRag')
  },
  updateRag({ commit }, payload) {
    commit('updateRag', payload)
  },
  updateMetadata({ commit }, payload) {
    commit('updateMetadata', payload)
  },
  updateRagProperty({ commit }, payload) {
    commit('updateRagProperty', payload)
  },
  updateNestedRagProperty({ commit }, payload) {
    commit('updateNestedRagProperty', payload)
  },
}

export default {
  namespaced: true,
  state: state(),
  getters,
  mutations,
  actions,
}
