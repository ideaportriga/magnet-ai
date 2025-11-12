import { fetchData } from '@shared'
import _ from 'lodash'

const state = () => ({
  api_tool: {
    name: '',
    system_name: '',
    description: '',
    id: '',
    variants: [],
    active_variant: null,
  },
  selectedApiToolVariant: null,
  apiToolSelectedProperty: null,
  initialApiTool: null,
})

const getters = {
  api_tool: (state) => state.api_tool,
  api_tool_variant: (state) => {
    return state.api_tool.variants?.find((el) => el.variant === state.selectedApiToolVariant)
  },
  selectedApiToolVariant: (state) => state.selectedApiToolVariant,
  isApiToolChanged(state) {
    if (!state.initialApiTool) return false
    return !_.isEqual(state.api_tool, state.initialApiTool)
  },
  initialApiTool: (state) => state.initialApiTool,
  apiToolSelectedProperty: (state) => state.apiToolSelectedProperty,
}

const mutations = {
  setSelectedApiToolVariant(state, payload) {
    state.selectedApiToolVariant = payload
  },
  setApiTool(state, payload) {
    state.api_tool = _.cloneDeep(payload)
    state.initialApiTool = _.cloneDeep(payload)
    state.selectedApiToolVariant = payload?.active_variant
  },
  updateApiToolProperty(state, payload) {
    state.api_tool[payload.key] = payload.value
  },
  updateNestedApiToolProperty(state, { path, value }) {
    const variant = state.api_tool.variants.find((el) => el.variant === state.selectedApiToolVariant)
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
      console.log('target', target)
      if (value === null) {
        delete target[lastKey]
      } else {
        target[lastKey] = value
      }
    }
  },
  activateApiToolVariant(state) {
    state.api_tool.active_variant = state.selectedApiToolVariant
  },
  revertApiToolChanges(state) {
    console.log('revertApiToolChanges', state.initialApiTool)
    state.api_tool = state.initialApiTool
    state.selectedApiToolVariant = state.initialApiTool?.active_variant
  },
  createApiToolVariant(state, variant = null) {
    if (!variant) variant = state.api_tool.variants.find((el) => el.variant === state.selectedApiToolVariant)
    const maxVariantNumber = state.api_tool.variants.reduce((max, el) => {
      const variantNumber = parseInt(el.variant.split('_')[1]) || 0
      return Math.max(max, variantNumber)
    }, 0)
    const newVariantKey = `variant_${maxVariantNumber + 1}`
    const newVariant = variant ? { ..._.cloneDeep(variant), variant: newVariantKey, description: '' } : { variant: newVariantKey }
    state.api_tool.variants.push(newVariant)
    state.selectedApiToolVariant = newVariantKey
  },
  setInitApiTool(state) {
    state.initialApiTool = _.cloneDeep(state.api_tool)
  },
  deleteApiToolVariant(state) {
    if (state.api_tool.variants.length > 1) {
      const index = state.api_tool.variants.findIndex((el) => el.variant === state.selectedApiToolVariant)
      state.api_tool.variants.splice(index, 1)
      state.selectedApiToolVariant = state.api_tool.variants[0].variant
      state.api_tool.active_variant = state.selectedApiToolVariant
    }
  },
}

const actions = {
  updateApiTool(context, payload) {
    context.commit('updateApiTool', payload)
  },
  updateApiToolProperty(context, payload) {
    context.commit('updateApiToolProperty', payload)
  },
  updateNestedApiToolProperty(context, payload) {
    console.log('payload', payload)
    context.commit('updateNestedApiToolProperty', payload)
  },
  setInitApiTool(context) {
    context.commit('setInitApiTool')
  },
  deleteApiToolVariant(context) {
    context.commit('deleteApiToolVariant')
  },
  saveApiTool(context) {
    // context.commit('saveApiTool')
    const apiTool = _.cloneDeep(context.state.api_tool)
    const id = apiTool.id
    const entity = 'api_tools'
    delete apiTool._metadata
    delete apiTool.id
    context.dispatch('chroma/update', { payload: { id, data: apiTool }, entity }, { root: true })
    context.commit('setInitApiTool')
  },
  revertApiToolChanges(context, payload) {
    context.commit('revertApiToolChanges')
  },
  async testApiTool(context, payload) {
    const res = await fetchData({
      method: 'POST',
      service: 'api_tools/test',
      credentials: 'include',
      body: JSON.stringify(payload),
      endpoint: context.state.config?.collections?.endpoint,
      headers: {
        'Content-Type': 'application/json',
      },
    })
    return res.json()
  },
}

export default {
  namespaced: true,
  state: state(),
  getters,
  mutations,
  actions,
}
