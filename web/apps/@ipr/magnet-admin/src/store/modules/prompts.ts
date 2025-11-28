import _ from 'lodash'

const state = () => ({
  promptTemplate: {
    system_name: '',
    description: '',
    id: '',
    variants: [],
    active_variant: null,
  },
  initPromptTemplate: null,
  selectedPromptTemplateVariant: null,
  promptTemplateTestSetItem: {},
})

const getters = {
  promptTemplateTestSetItem: (state) => state.promptTemplateTestSetItem,
  promptTemplateVariant: (state) => {
    return state.promptTemplate.variants?.find((el) => el.variant === state.selectedPromptTemplateVariant)
  },
  promptTemplate: (state) => state.promptTemplate,
  selectedPromptTemplateVariant: (state) => state.selectedPromptTemplateVariant,
  isPromptTemplateChanged(state) {
    if (!state.initPromptTemplate) return false
    return !_.isEqual(state.promptTemplate, state.initPromptTemplate)
  },
}

const mutations = {
  setPromptTemplateTestSetItem(state, payload) {
    state.promptTemplateTestSetItem = payload
  },
  revertPromptTemplateChanges(state) {
    state.promptTemplate = _.cloneDeep(state.initPromptTemplate)
  },
  setSelectedPromptTemplateVariant(state, payload) {
    state.selectedPromptTemplateVariant = payload
  },
  setInitPromptTemplate(state) {
    state.initPromptTemplate = _.cloneDeep(state.promptTemplate)
  },
  setPromptTemplate(state, payload) {
    state.promptTemplate = _.cloneDeep(payload)
    state.initPromptTemplate = _.cloneDeep(payload)
    state.selectedPromptTemplateVariant = payload?.active_variant
  },
  updatePromptTemplate(state, payload) {
    state.promptTemplate = { ...state.promptTemplate, ...payload }
  },
  updateMetadata(state, payload) {
    state.promptTemplate._metadata = { ...state.promptTemplate._metadata, ...payload }
  },
  updatePromptTemplateProperty(state, { key, value }) {
    state.promptTemplate[key] = value
  },
  updateNestedPromptTemplateProperty(state, { path, value }) {
    const variant = state.promptTemplate.variants.find((el) => el.variant === state.selectedPromptTemplateVariant)
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

  createPromptTemplateVariant(state, { baseVariantKey = null } = {}) {
    const baseVariant = state.promptTemplate.variants.find((el) => el.variant === state.selectedPromptTemplateVariant)

    const maxVariantNumber = state.promptTemplate.variants.reduce((max, el) => {
      const variantNumber = parseInt(el.variant.split('_')[1]) || 0
      return Math.max(max, variantNumber)
    }, 0)
    const newVariantKey = `variant_${maxVariantNumber + 1}`

    const newVariant = baseVariant ? { ..._.cloneDeep(baseVariant), variant: newVariantKey, description: '' } : { variant: newVariantKey }

    state.promptTemplate.variants.push(newVariant)

    state.selectedPromptTemplateVariant = newVariantKey
  },
  deletePromptTemplateVariant(state) {
    if (state.promptTemplate.variants.length > 1) {
      const index = state.promptTemplate.variants.findIndex((el) => el.variant === state.selectedPromptTemplateVariant)

      if (index !== -1) {
        const isActiveVariant = state.selectedPromptTemplateVariant === state.promptTemplate.active_variant

        state.promptTemplate.variants.splice(index, 1)

        const newIndex = index === 0 ? 0 : index - 1
        state.selectedPromptTemplateVariant = state.promptTemplate.variants[newIndex].variant

        if (isActiveVariant) {
          state.promptTemplate.active_variant = state.selectedPromptTemplateVariant
        }
      }
    }
  },
  activatePromptTemplateVariant(state) {
    state.promptTemplate.active_variant = state.selectedPromptTemplateVariant
  },
}

const actions = {
  async savePromptTemplate({ commit, dispatch, getters }) {
    const entity = 'promptTemplates'
    const obj = { ...getters.promptTemplate }
    delete obj._metadata
    delete obj.id

    if (getters.promptTemplate?.created_at) {
      await dispatch('chroma/update', { payload: { id: getters.promptTemplate.id, data: JSON.stringify(obj) }, entity }, { root: true })
    } else {
      await dispatch('chroma/create', { payload: getters.promptTemplate, entity }, { root: true })
    }
    commit('setInitPromptTemplate')
  },
}

export default {
  namespaced: true,
  state: state(),
  getters,
  mutations,
  actions,
}
