import chroma from '@/config/chroma'
import router from '@/router'
import { generateGetters } from '@/store/utils'
import { transformChromaRequest, transformChromaResponse } from '@shared/utils/chromaUtils'
import { ActionContext } from 'vuex'

interface EntityState {
  items: any[]
  selected: any | null
  searchString: string
  filterObject: any
  publicSelected: any[]
  loading: boolean
  config?: any
  api?: any
  keyField?: { field: string; urlKey: string }
  pagination?: { sortBy: string; descending: boolean; page: number; rowsPerPage: number; rowsNumber?: number }
}

interface ChromaState {
  [key: string]: EntityState
}

const state = (): ChromaState => {
  const initialState: ChromaState = {}
  Object.keys(chroma).forEach((key) => {
    initialState[key] = {
      ...chroma[key],
      items: [],
      selected: null,
      searchString: '',
      filterObject: {},
      publicSelected: [],
      loading: false,
    }
  })
  return initialState
}

let getters = {
  columns: (state: ChromaState, getters: any) => (entity: string) =>
    Object.values(getters[entity].config).sort((a: any, b: any) => a.columnNumber - b.columnNumber),
  requiredFields: (state: ChromaState, getters: any) => (entity: string) =>
    Object.values(getters[entity].config)
      .filter(({ validate }: any) => validate)
      .map(({ name }: any) => name),
  visibleColumns: (state: ChromaState, getters: any) => (entity: string) =>
    getters
      .columns(entity)
      .filter(({ display }: any) => display)
      .map(({ name }: any) => name),
  publicItems: (state: ChromaState, getters: any) => (entity: string) => {
    return (
      state[entity]?.items.map((item: any) => ({
        ...item,
        value: item.id,
        label: item.name,
      })) || []
    )
  },

  publicSelectedOptionsList: (state: ChromaState, getters: any) => (entity: string) => {
    const publicItems = getters.publicItems(entity)
    const selected = state[entity]?.publicSelected
    return publicItems.filter((item: any) => selected.some((value: any) => value === item.value))
  },
  selectedRow: (state: ChromaState, getters: any) => (entity: string) => {
    const selected = getters[entity].selected
    const items = getters[entity].items
    const field = state[entity].keyField?.field ?? ''
    const item = items.find((el: any) => el[field] === selected)
    return item ?? null
  },
  visibleRows: (state: ChromaState, getters: any) => (entity: string) => {
    const { items = [], searchString = '' } = getters[entity] || {}

    const searchTerms = searchString.includes(',')
      ? searchString
          .split(',')
          .map((term) => term.trim().toLowerCase())
          .filter((term) => term)
      : [searchString.toLowerCase()]

    const containsSearchTerm = (value: any): boolean => {
      if (typeof value === 'string') {
        const lowerCaseVal = value.toLowerCase()
        return searchTerms.some((term) => lowerCaseVal.includes(term))
      }
      if (typeof value === 'object' && value !== null) {
        return Object.values(value).some(containsSearchTerm)
      }
      return false
    }

    return items.filter((el: any) => {
      return Object.values(el).some(containsSearchTerm)
    })
  },

  formatFunctions: (state: ChromaState, getters: any) => (entity: string) => {
    const config = getters[entity].config
    if (!config) {
      return {
        req: () => {},
        res: () => {},
      }
    }
    return {
      req: transformChromaRequest.bind(config),
      res: transformChromaResponse.bind(config),
    }
  },
}

const mutations = {
  set(state: ChromaState, { payload, entity }: { payload: any; entity: string }) {
    Object.entries(payload).forEach(([key, value]) => {
      state[entity][key] = value
    })
  },
  delete(state: ChromaState, { id, entity }: { id: any; entity: string }) {
    state[entity].items = state[entity].items.filter((item) => item.id !== id)
  },
  add(state: ChromaState, { item, entity }: { item: any; entity: string }) {
    state[entity].items.push(item)
  },
  setLoading(state: ChromaState, { entity, value }: { entity: string; value: boolean }) {
    state[entity].loading = value
  },
  resetLoading(state: ChromaState, { entity }: { entity: string }) {
    state[entity].loading = false
  },
  updateItem(state: ChromaState, { entity, index, item }: { entity: string; index: number; item: any }) {
    console.log('updateItem', entity, index, item)
    if (index !== -1) {
      state[entity].items.splice(index, 1, item[0])
    } else {
      state[entity].items.push(item[0])
    }
  },
}

const actions = {
  async getPaginated(
    { state, commit, rootGetters, getters }: ActionContext<ChromaState, any>,
    { payload, entity }: { payload: any; entity: string }
  ) {
    commit('setLoading', { entity, value: true })

    const endpoint = rootGetters.config?.collections?.endpoint
    const service = rootGetters.config?.collections?.service || ''
    const req = state[entity].api
    const defaultCollection = rootGetters.config?.collections?.default || ''
    const format = getters.formatFunctions(entity).res

    try {
      const { items, total } = await req.getPaginated(service, endpoint, payload)
      if (state?.[entity]?.pagination) {
        commit('set', {
          payload: { pagination: { ...payload.pagination, rowsNumber: total }},
          entity,
        })
      }
      if (!state?.[entity]?.publicSelected?.length) {
        commit('set', {
          payload: { publicSelected: [defaultCollection] },
          entity,
        })
      }
      commit('set', {
        payload: {
          items: format(items),
        },
        entity,
      })
    } catch (errorMessage) {
      commit('set', { errorMessage }, { root: true })
    } finally {
      commit('resetLoading', { entity })
    }
  },

  async get({ state, commit, rootGetters, getters }: ActionContext<ChromaState, any>, { payload, entity }: { payload: any; entity: string }) {
    commit('setLoading', { entity, value: true })
    const endpoint = rootGetters.config?.collections?.endpoint
    const service = rootGetters.config?.collections?.service || ''
    const req = state[entity].api
    const defaultCollection = rootGetters.config?.collections?.default || ''
    const format = getters.formatFunctions(entity).res

    try {
      const items = await req.get(service, endpoint, payload)
      if (!state?.[entity]?.publicSelected?.length) {
        commit('set', {
          payload: { publicSelected: [defaultCollection] },
          entity,
        })
      }
      commit('set', {
        payload: {
          items: format(items),
        },
        entity,
      })
    } catch (errorMessage) {
      commit('set', { errorMessage }, { root: true })
    } finally {
      commit('resetLoading', { entity })
    }
  },

  async getDetail({ state, commit, rootGetters, getters }: ActionContext<ChromaState, any>, { payload, entity }: { payload: any; entity: string }) {
    commit('setLoading', { entity, value: true })
    const endpoint = rootGetters.config?.collections?.endpoint
    const service = rootGetters.config?.collections?.service || ''
    const req = state[entity].api
    const format = getters.formatFunctions(entity).res

    try {
      const detailItem = await req.getDetail(service, endpoint, payload)
      const formattedDetail = format(detailItem)

      const index = state[entity].items.findIndex((item: any) => item.id === payload.id)
      const updatedItem = { ...formattedDetail }
      commit('updateItem', { entity, index, item: updatedItem })
    } catch (errorMessage) {
      // commit('set', { errorMessage }, { root: true })
    } finally {
      commit('resetLoading', { entity })
    }
  },

  async update({ rootGetters, dispatch, commit, state }: ActionContext<ChromaState, any>, { payload, entity }: { payload: any; entity: string }) {
    commit('setLoading', { entity, value: true })
    const endpoint = rootGetters.config?.collections?.endpoint
    const service = rootGetters.config?.collections?.service || ''
    const req = state[entity].api

    try {
      await req.update(service, endpoint, { ...payload, entity }, { dispatch })
      return true
    } catch (errorMessage) {
      commit('set', { errorMessage }, { root: true })
      return false
    } finally {
      commit('resetLoading', { entity })
    }
  },

  async refresh({ commit, rootGetters, dispatch, state }: ActionContext<ChromaState, any>, { payload, entity }: { payload: any; entity: string }) {
    commit('setLoading', { entity, value: true })
    const endpoint = rootGetters.config?.collections?.endpoint
    const service = rootGetters.config?.collections?.service || ''
    const req = state[entity].api

    try {
      await req.refresh(service, endpoint, payload, { dispatch })
      return true
    } catch (errorMessage) {
      commit('set', { errorMessage }, { root: true })
      return false
    } finally {
      commit('resetLoading', { entity })
    }
  },

  async create({ rootGetters, dispatch, commit, state }: ActionContext<ChromaState, any>, { payload, entity }: { payload: any; entity: string }) {
    commit('setLoading', { entity, value: true })
    const endpoint = rootGetters.config?.collections?.endpoint
    const service = rootGetters.config?.collections?.service || ''
    const req = state[entity].api

    try {
      const collection = await req.create(service, endpoint, payload)
      dispatch('get', { entity })
      return collection
    } catch (errorMessage) {
      commit('set', { errorMessage }, { root: true })
      return false
    } finally {
      commit('resetLoading', { entity })
    }
  },

  async delete({ rootGetters, commit, state }: ActionContext<ChromaState, any>, { payload, entity }: { payload: any; entity: string }) {
    commit('setLoading', { entity, value: true })
    const endpoint = rootGetters.config?.collections?.endpoint
    const service = rootGetters.config?.collections?.service || ''
    const req = state[entity].api

    try {
      const id = await req.delete(service, endpoint, payload)
      commit('delete', { entity, id })
      return true
    } catch (errorMessage) {
      commit('set', { errorMessage }, { root: true })
      return false
    } finally {
      commit('resetLoading', { entity })
    }
  },


  selectFromRouter(
    { state, commit, dispatch }: ActionContext<ChromaState, any>,
    { payload, entity, detail }: { payload: any; entity: string; detail: boolean }
  ) {
    console.log('selectFromRouter', payload, entity, detail)
    if (!payload || !entity) return

    commit('setLoading', { entity, value: true })
    const keyField = state?.[entity]?.keyField?.urlKey ?? ''
    const selected = payload[keyField]
    console.log('selected', selected)
    if (selected) {
      commit('set', { payload: { selected }, entity })
    } else {
      commit('set', { payload: { selected: null }, entity })
    }

    if (detail && selected) {
      console.log('detail & selected', detail, selected)
      dispatch('getDetail', { payload: { id: selected }, entity })
    } else {
      commit('resetLoading', { entity })
    }
  },

  selectRecord({ getters }: ActionContext<ChromaState, any>, { payload, entity }: { payload: any; entity: string }) {
    const key = getters[entity][`keyField`].urlKey
    const params = { ...router.currentRoute.value.params }
    if (payload) params[key] = payload
    else delete params[key]

    router.replace({ ...router.currentRoute.value, params })
  },
  reset({ commit }: ActionContext<ChromaState, any>, { entity }: { entity: string }) {
    commit('set', { payload: { items: [] }, entity })
  },
}

export const [baseGetters, chromaWrapperGetters] = generateGetters({
  state: state(),
  entities: [
    'collections',
    'documents',
    'rag_tools',
    'promptTemplates',
    'ai_apps',
    'ai_app_tabs',
    'evaluation_sets',
    'evaluation_jobs',
    'observability_traces',
    'retrieval',
    'model',
    'provider',
    'assistant_tools',
    'api_tools',
    'api_tool_providers',
    'agents',
    'jobs',
    'mcp_servers',
  ],
  namespace: 'chroma',
  getters,
})

getters = {
  ...getters,
  ...baseGetters,
}

const chromaStore = {
  namespaced: true,
  getters,
  mutations,
  actions,
  state: state(),
}

export default chromaStore
