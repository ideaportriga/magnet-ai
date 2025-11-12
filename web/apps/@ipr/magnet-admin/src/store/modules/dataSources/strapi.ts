import strapi from '@/config/strapi/config'
import router from '@/router'
import { generateGetters } from '@/store/utils'
import { transformStrapiRequest, transformStrapiResponse } from '@shared/utils/strapiUtils'

const state = () => {
  const state = {}
  Object.keys(strapi).forEach((key) => {
    state[key] = {
      ...strapi[key],
      items: undefined,
      selected: null,
      pinned: [],
    }
  })
  return state
}

let getters = {
  requiredFields: (state, getters) => (entity) =>
    Object.values(getters[entity].config)
      .filter(({ validate }: any) => validate)
      .map(({ name }: any) => name),
  selectedRow: (state, getters) => (entity) => {
    const selected = getters[entity].selected
    const items = getters[entity].items
    const field = state[entity].keyField.field
    const item = items?.find((el) => String(el[field]) === String(selected))
    return item ?? null
  },
  formatFunctions: (getters) => (entity) => {
    const config = getters[entity].config
    if (!config) {
      return {
        req: () => {},
        res: () => {},
      }
    }
    return {
      req: transformStrapiRequest.bind(config),
      res: transformStrapiResponse.bind(config),
    }
  },
  // promptOrder: (state, getters) => (entity) => {
  //   return getters.selectedRow(entity)?.prompts?.map(({ id }) => id)
  // }
}

const mutations = {
  set(state, { payload, entity }) {
    Object.entries(payload).forEach(([key, value]) => {
      state[entity][key] = value
    })
  },
  deleteItem(state, { id, entity }) {
    state[entity].items = state[entity].items?.filter((item) => item.id !== id)
  },
  addItem(state, { item, entity }) {
    state[entity].items.push(item)
  },
  replaceItem(state, { newItem, entity }) {
    state[entity].items = state[entity].items?.map((item) => (item.id === newItem.id ? newItem : item))
  },
}
const actions = {
  set({ commit }, { payload, entity }) {
    commit('set', { payload, entity })
  },
  async get({ commit, state, rootGetters, getters }, { entity, payload }) {
    const {
      endpoint,
      headers,
      credentials,
      [entity]: { service, queryParams = '' },
    } = rootGetters.config?.strapi
    const req = state[entity].api
    const format = getters.formatFunctions(entity).res

    await req
      .get(service, endpoint, queryParams, headers, payload, credentials)
      .then((data) => {
        commit('set', {
          payload: {
            items: data,
          },
          entity,
        })
      })
      .catch((errorMessage) => {
        commit(
          'set',
          { errorMessage },
          {
            root: true,
          }
        )
      })
  },
  async update({ rootGetters, dispatch, commit, state, getters }, { payload, entity }) {
    const {
      endpoint,
      headers,
      [entity]: { service, queryParams = '' },
    } = rootGetters.config?.strapi
    const { id, data } = payload
    const format = getters.formatFunctions(entity)?.res
    const req = state[entity].api
    return await req
      .update(`${service}/${id}`, endpoint, headers, data)
      .then((newItem) => {
        if (entity === 'prompts') commit('replaceItem', { entity, newItem: format([newItem])[0] })
        dispatch('get', { entity: 'templates' })
        return true
      })
      .catch((errorMessage) => {
        commit('set', { errorMessage }, { root: true })
        return false
      })
  },
  async create({ rootGetters, commit, state, dispatch, getters }, { payload, entity }) {
    const {
      endpoint,
      headers,
      [entity]: { service, queryParams = '' },
    } = rootGetters.config?.strapi
    const req = state[entity].api
    const format = getters.formatFunctions(entity).res
    return await req
      .create(service, endpoint, headers, payload)
      .then(async (id) => {
        //const item = format([data])[0]
        await dispatch('get', { entity: 'templates' })
        return id
      })
      .catch((errorMessage) => {
        commit('set', { errorMessage }, { root: true })
        return false
      })
  },
  async delete({ rootGetters, commit, state, dispatch, getters }, { payload, entity }) {
    const {
      endpoint,
      headers,
      [entity]: { service, queryParams = '' },
    } = rootGetters.config?.strapi
    const { id } = payload
    const req = state[entity].api
    return await req
      .delete(`${service}/${id}`, endpoint, headers)
      .then(async (id) => {
        // commit('deleteItem', { entity, id })
        // if (entity === 'prompts')
        await dispatch('get', { entity: 'templates' })
        return true
      })
      .catch((errorMessage) => {
        commit('set', { errorMessage }, { root: true })
        return false
      })
  },
  selectFromRouter({ state, commit }, { payload }) {
    if (!payload) return
    const keys = Object.keys(state).map((key) => {
      return {
        entity: key,
        keyField: state[key].keyField.urlKey,
      }
    })
    keys.forEach((key) => {
      const entity = key.entity
      const selected = payload[key.keyField]
      if (selected) commit('set', { payload: { selected }, entity })
      else commit('set', { payload: { selected: null }, entity })
    })
  },
  selectRecord({ getters }, { payload, entity }) {
    // payload = String(payload)
    const key = getters[entity][`keyField`].urlKey
    const params = { ...router.currentRoute.value.params }
    if (payload) params[key] = String(payload)
    else delete params[key]

    router.replace({ ...router.currentRoute.value, params })
  },
  async copy({ rootGetters, commit, state, dispatch, getters }, { payload, entity }) {
    // CONFIG
    const {
      endpoint,
      headers,
      templates: { service: templatesService, queryParams: templatesQueryParams = '' },
      prompts: { service: promptsService, queryParams: promptsQueryParams = '' },
    } = rootGetters.config?.strapi
    const reqTemplate = state.templates.api
    const reqPrompt = state.prompts.api
    const keysRemove = ['createdAt', 'publishedAt', 'updatedAt', 'id']
    if (entity === 'templates') {
      // GET PROMPT DATA
      const newId = await reqTemplate.create(templatesService, endpoint, headers, {
        category: payload?.category ?? null,
        description: payload?.description ?? null,
        iconName: payload?.iconName ?? null,
        title: `${payload?.title} (copy)` ?? null,
        pinned: false,
        prompts: payload?.prompts ?? null,
      })
      // CREATE PROMPTS
      // const createPromptsPromises = payload.prompts.map(async (prompt) => {
      //   let edited = prompt
      //   keysRemove.forEach((key) => {
      //     delete edited[key]
      //   })

      //   return reqPrompt.create(promptsService, endpoint, headers, {
      //     ...edited,
      //     template: {
      //       connect: [newTemplate.id]
      //     }
      //   })
      // })
      // await Promise.all(createPromptsPromises)
      // REFRESH PROMPTS,
      await dispatch('get', { entity: 'templates' })
      //RETURN NEW ID
      return newId
    } else {
      const edited = payload
      // REMOVE UNNECESSARY KEYS
      keysRemove.forEach((key) => {
        delete edited[key]
      })
      // CREATE A COPY
      const newPrompt = await reqPrompt.create(promptsService, endpoint, headers, {
        ...edited,
        name: `${payload?.name} (copy)` ?? null,
      })
      // RETURN COPY ID
      return newPrompt.id
    }
  },
}

export const [baseGetters, strapiWrapperGetters] = generateGetters({
  state: state(),
  entities: ['templates', 'prompts'],
  namespace: 'strapi',
  getters,
})

getters = {
  ...getters,
  ...baseGetters,
}

const strapiStore = {
  namespaced: true,
  getters,
  mutations,
  actions,
  state: state(),
}
export default strapiStore
