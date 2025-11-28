import _ from 'lodash'

// state
const state = () => ({
  ai_app: {
    name: '',
    system_name: '',
    description: '',
    tabs: [],
  },
  initAIApp: null,
})

// getters
const getters = {
  ai_app: (state) => state.ai_app,

  isAIAppChanged: (state) => {
    if (!state.initAIApp) return false
    return !_.isEqual(state.ai_app, state.initAIApp)
  },
  isCancelAvailable(state, getters) {
    return !getters.ai_app?._metadata
  },
  getTabBySystemName:
    (state) =>
    (system_name, child_system_name = null) => {
      const tab = state.ai_app.tabs.find((el) => el.system_name === system_name)
      if (child_system_name) {
        return tab.children?.find((el) => el.system_name === child_system_name)
      }
      return tab
    },
}

// mutations
const mutations = {
  revertAIAppChanges(state) {
    state.ai_app = _.cloneDeep(state.initAIApp)
  },
  setInitAIApp(state, payload) {
    state.initAIApp = _.cloneDeep(state.ai_app)
  },
  addAIAppTab(state, payload) {
    if (!Array.isArray(state?.ai_app?.tabs)) {
      state.ai_app['tabs'] = []
    }

    // update if tab already exists
    const tab = state.ai_app.tabs.find((el) => el.system_name == payload.system_name)
    if (tab) {
      Object.assign(tab, payload)
      return
    }

    state.ai_app.tabs.push(payload)
  },
  deleteAIAppTab(state, payload) {
    if (typeof payload === 'string') {
      state.ai_app.tabs = state.ai_app.tabs.filter((el) => el.system_name !== payload)
      return
    }
    const parentName = payload[0]
    const systemName = payload[1]
    state.ai_app.tabs = state.ai_app.tabs.map((el) => {
      if (el.system_name === parentName) {
        el.children = el.children.filter((el) => el.system_name !== systemName)
      }
      return el
    })
  },
  updateAIAppTabProperty(state, { system_name, child_system_name = null, newProperties }) {
    console.log('updateAIAppTabProperty', system_name, newProperties)
    const tab = state.ai_app.tabs.find((el) => el.system_name === system_name)
    if (tab) {
      if (child_system_name) {
        const child = tab.children.find((el) => el.system_name === child_system_name)
        Object.assign(child, newProperties)
      } else {
        Object.assign(tab, newProperties)
      }
    }
  },
  setAIApp(state, payload) {
    state.initAIApp = _.cloneDeep(payload)
    state.ai_app = _.cloneDeep(payload)
  },
  updateAIApp(state, payload) {
    state.ai_app = { ...state.ai_app, ...payload }
  },
  updateMetadata(state, payload) {
    state.ai_app._metadata = { ...state.ai_app._metadata, ...payload }
  },
  updateAIAppProperty(state, { key, value }) {
    state.ai_app[key] = value
  },
  setAIAppTabs(state, payload) {
    state.ai_app.tabs = payload
  },

  updateNestedAIAppProperty(state, { path, value }) {
    const keys = path.split('.')
    let target = state.ai_app
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
  async saveAIApp({ commit, dispatch, getters }, payload) {
    const entity = 'ai_apps'
    if (getters.ai_app?.created_at) {
      const obj = { ...getters.ai_app }
      delete obj._metadata
      delete obj.id
      await dispatch('chroma/update', { payload: { id: getters.ai_app.id, data: obj }, entity }, { root: true })
    } else {
      await dispatch('chroma/create', { payload: getters.ai_app, entity }, { root: true })
    }
    commit('setInitAIApp')
  },
  updateAIApp({ commit }, payload) {
    commit('updaterag', payload)
  },
  updateMetadata({ commit }, payload) {
    commit('updateMetadata', payload)
  },
  updateAIAppProperty({ commit }, payload) {
    commit('updateAIAppProperty', payload)
  },
  updateNestedAIAppProperty({ commit }, payload) {
    commit('updateNestedAIAppProperty', payload)
  },
}

export default {
  namespaced: true,
  state: state(),
  getters,
  mutations,
  actions,
}
