import _ from 'lodash'

const state = () => ({
  provider: {
    id: '',
    name: '',
    description: null,
    system_name: '',
    category: null,
    type: '',
    connection_config: {},
    secrets_encrypted: {},
    metadata_info: {},
    created_at: null,
    updated_at: null,
    created_by: null,
    updated_by: null,
  },
  initProvider: null,
})

const getters = {
  provider: (state) => state.provider,
  isProviderChanged(state) {
    if (!state.initProvider) return false
    return !_.isEqual(state.provider, state.initProvider)
  },
}

const mutations = {
  revertProviderChanges(state) {
    state.provider = _.cloneDeep(state.initProvider)
  },
  setInitProvider(state) {
    state.initProvider = _.cloneDeep(state.provider)
  },
  setProvider(state, payload) {
    state.provider = _.cloneDeep(payload)
    state.initProvider = _.cloneDeep(payload)
  },
  updateProvider(state, payload) {
    state.provider = { ...state.provider, ...payload }
  },
  updateProviderProperty(state, { key, value }) {
    state.provider[key] = value
  },
  updateNestedProviderProperty(state, { path, value }) {
    const keys = path.split('.')
    let target = state.provider

    for (let i = 0; i < keys.length - 1; i++) {
      if (!(keys[i] in target) || target[keys[i]] === null) {
        target[keys[i]] = {}
      }
      target = target[keys[i]]
    }

    const lastKey = keys[keys.length - 1]

    if (value === null) {
      delete target[lastKey]
    } else {
      target[lastKey] = value
    }
  },
}

const actions = {
  async saveProvider({ commit, dispatch, getters }) {
    const entity = 'provider'
    const obj = { ...getters.provider }
    
    // Remove read-only fields
    delete obj.id
    delete obj.created_at
    delete obj.updated_at
    delete obj.created_by
    delete obj.updated_by

    if (getters.provider?.created_at) {
      // Update existing provider
      await dispatch('chroma/update', { payload: { id: getters.provider.id, data: JSON.stringify(obj) }, entity }, { root: true })
    } else {
      // Create new provider
      await dispatch('chroma/create', { payload: obj, entity }, { root: true })
    }
    commit('setInitProvider')
  },
}

export default {
  state: state(),
  getters,
  mutations,
  actions,
}
