import _ from 'lodash'

const emptyModule = {
  getters: {},
  actions: {},
  mutations: {},
  state: {},
}

export const mergeModules = (modules = []) => {
  let merged = emptyModule
  modules.forEach((module) => {
    ;['state', 'getters', 'actions', 'mutations'].forEach((prop) => {
      merged[prop] = { ...merged[prop], ...module[prop] }
    })
  })
  return merged
}

export const getByPath = (object, path, value) => {
  // If path is not defined or it has false value
  if (!path) return undefined
  // Check if path is string or array. Regex : ensure that we do not have '.' and brackets
  const pathArray = Array.isArray(path) ? path : path.split(/[,[\].]/g).filter(Boolean)
  // Find value if exist return otherwise return undefined value;
  return pathArray.reduce((prevObj, key) => prevObj && prevObj[key], object) || value
}

export const generateBaseGeters = (state, entities = []) => {
  const baseGetters = {}
  Object.keys(state).forEach((key) => {
    if (entities.includes(key)) {
      baseGetters[key] = (state) => state[key] //?.[namespace]?.[key]
    } else baseGetters[key] = (state) => () => state[key]
  })
  return baseGetters
}
export const generateWrapperGetters = (baseState, entities, namespace, wrapGetters) => {
  return {
    [namespace]: (getters, rootGetters) => {
      const wrapperGetters = {}
      entities.forEach((entity) => {
        const keys = Object.keys(baseState[entity])
        wrapperGetters[entity] = {}
        keys.forEach((key) => {
          wrapperGetters[entity][key] = rootGetters[`${namespace}/${entity}`][key]
        })
        Object.keys(wrapGetters).forEach((key) => {
          wrapperGetters[entity][key] = rootGetters[`${namespace}/${key}`](entity)
        })
      })
      return wrapperGetters
    },
  }
}

export const generateGetters = ({ state, entities, namespace, getters }) => {
  const baseGetters = generateBaseGeters(state, entities, namespace)
  const entityGetters = generateWrapperGetters(state, entities, namespace, getters)
  return [baseGetters, entityGetters]
}
export const createEntityStore = (namespace) => {
  // state
  const state = () => ({
    entity: {
      name: '',
      code: '',
      description: '',
    },
    initialEntity: null,
  })

  // getters
  const getters = {
    entity: (state) => state.entity,

    isEntityChanged(state) {
      if (!state.initialEntity) return false
      return !_.isEqual(state.entity, state.initialEntity)
    },

    isCancelAvailable(state, getters) {
      return !getters.entity?._metadata
    },
  }

  // mutations
  const mutations = {
    setInitEntity(state) {
      state.initialEntity = _.cloneDeep(state.entity)
    },
    setEntity(state, payload) {
      state.entity = payload
      state.initialEntity = _.cloneDeep(payload)
    },
    updateEntity(state, payload) {
      state.entity = { ...state.entity, ...payload }
    },
    updateMetadata(state, payload) {
      state.entity._metadata = { ...state.entity._metadata, ...payload }
    },
    updateEntityProperty(state, { key, value }) {
      state.entity[key] = value
    },
    updateNestedEntityProperty(state, { path, value }) {
      _.set(state.entity, path, value)
    },
    revertEntity(state) {
      state.entity = _.cloneDeep(state.initialEntity)
    },
  }

  // actions
  const actions = {
    async saveEntity({ commit, dispatch, getters }, payload) {
      // TO FIX: This is a temporary solution. We need to find a better way to handle relationships between chroma and inner entities
      let entity = namespace
      if (namespace === 'modelConfig') {
        entity = 'model'
      }

      const obj = { ...getters.entity }

      // Convert numeric price fields to strings for model entities
      if (namespace === 'modelConfig') {
        const priceFields = [
          'price_input', 'price_cached', 'price_output', 'price_reasoning',
          'price_standard_input_unit_count', 'price_cached_input_unit_count',
          'price_standard_output_unit_count', 'price_reasoning_output_unit_count'
        ]
        
        priceFields.forEach(field => {
          if (obj[field] !== undefined && obj[field] !== null && obj[field] !== '') {
            obj[field] = String(obj[field])
          }
        })
      }

      if (getters.entity?.created_at) {
        // Remove metadata and audit fields - they are managed by backend
        delete obj._metadata
        delete obj.created_at
        delete obj.updated_at
        delete obj.created_by
        delete obj.updated_by
        
        // Remove configs if empty
        if (obj.configs && typeof obj.configs === 'object' && Object.keys(obj.configs).length === 0) {
          delete obj.configs
        }
        
        await dispatch('chroma/update', { payload: { id: getters.entity.id, data: JSON.stringify(obj) }, entity }, { root: true })
      } else {
        delete obj.id
        delete obj._metadata
        delete obj.created_at
        delete obj.updated_at
        delete obj.created_by
        delete obj.updated_by
        
        // Remove configs if empty
        if (obj.configs && typeof obj.configs === 'object' && Object.keys(obj.configs).length === 0) {
          delete obj.configs
        }
        
        await dispatch('chroma/create', { payload: JSON.stringify(obj), entity }, { root: true })
      }
      commit('setInitEntity')
    },
    updateEntity({ commit }, payload) {
      commit('updateEntity', payload)
    },
    updateMetadata({ commit }, payload) {
      commit('updateMetadata', payload)
    },
    updateEntityProperty({ commit }, payload) {
      commit('updateEntityProperty', payload)
    },
    updateNestedEntityProperty({ commit }, payload) {
      commit('updateNestedEntityProperty', payload)
    },
  }

  return {
    namespaced: true,
    state: state(),
    getters,
    mutations,
    actions,
  }
}

export default createEntityStore
