import _ from 'lodash'
import { fetchData } from '@shared'

// state
const state = () => ({
  authenticated: false,
  sourceSystem: undefined,
  sourceSystemUserName: undefined,
  globalLoading: true,
  errorMessage: undefined,
  config: undefined,
  panelOpenBlock: undefined,
  appVisible: true,
})

// getters
const getters = {
  authenticated: (state) => state.authenticated,
  sourceSystem: (state) => state.sourceSystem,
  sourceSystemUserName: (state) => state.sourceSystemUserName,
  globalLoading: (state) => state.globalLoading,
  errorMessage: (state) => state.errorMessage,
  appVisible: (state) => state.appVisible,
  config: (state) => state.config,
  prompts: (state, getters) => getters['chroma/promptTemplates'].items,
  panelOpenBlock: (state) => state.panelOpenBlock,
}

// mutations
const mutations = {}

// actions
const actions = {
  async loadConfig({ commit }) {
    commit('set', { globalLoading: true })

    const jsonConfigFileName = 'config/main.json'
    const response = await fetchData({
      endpoint: `${window.__vite_public_path__ ?? ''}${jsonConfigFileName}`,
    })

    if (response.ok) {
      const mainConfig = await response.json()

      const { auth: authRaw, api: apiRaw } = mainConfig
      const auth = {
        ...(authRaw ?? {}),
        enabled: String(authRaw?.enabled).toLowerCase() == 'true',
      }

      const aiBridgeUrlBase = apiRaw.aiBridge.baseUrl
      const aiBridgeUrlCommon = `${aiBridgeUrlBase}/api`

      const api = {
        apiRaw,
        aiBridge: {
          baseUrl: aiBridgeUrlBase,
          urlCommon: aiBridgeUrlCommon,
          urlAdmin: `${aiBridgeUrlCommon}/admin`,
          urlUser: `${aiBridgeUrlCommon}/user`,
        },
      }

      const environment = mainConfig.environment ?? ''
      const aiBridgeCredentials = (auth?.enabled ?? true) ? 'include' : null
      const config = {
        auth,
        environment,
        api,
        panel: {
          baseUrl: mainConfig.panel?.baseUrl ?? window.location.origin,
        },
        admin: {
          baseUrl: mainConfig.admin?.baseUrl ?? window.location.origin,
        },
        search: {
          endpoint: api.aiBridge.urlAdmin,
          credentials: aiBridgeCredentials,
          service: 'search',
        },
        rag: {
          endpoint: api.aiBridge.urlAdmin,
          credentials: aiBridgeCredentials,
          service: 'rag_tools',
        },
        model: {
          endpoint: api.aiBridge.urlAdmin,
          credentials: aiBridgeCredentials,
          service: 'models',
        },
        retrieval: {
          endpoint: api.aiBridge.urlAdmin,
          credentials: aiBridgeCredentials,
          service: 'retrieval',
        },
        agent: {
          endpoint: api.aiBridge.urlAdmin,
          credentials: aiBridgeCredentials,
          service: 'agents',
        },
        scheduler: {
          endpoint: api.aiBridge.urlAdmin,
          credentials: aiBridgeCredentials,
          service: 'scheduler',
        },
        agent_conversations: {
          endpoint: api.aiBridge.urlUser,
          credentials: aiBridgeCredentials,
          service: 'agent_conversations',
        },
        collections: {
          endpoint: api.aiBridge.urlAdmin,
          credentials: aiBridgeCredentials,
          service: 'collections',
          hidden: [],
          default: 'TODO',
        },
        documentSemanticSearch: {
          endpoint: api.aiBridge.urlAdmin,
          credentials: aiBridgeCredentials,
          service: 'rag/retrieve',
        },
        chatCompletion: {
          endpoint: api.aiBridge.urlAdmin,
          credentials: aiBridgeCredentials,
          service: 'prompt_templates/test',
          inputs: {
            model: 'gpt-35-turbo',
            temperature: 1,
            topP: 1,
          },
        },
        prompts: {
          endpoint: api.aiBridge.urlAdmin,
          credentials: aiBridgeCredentials,
          service: 'prompt_templates',
          headers: {
            'Content-Type': 'application/json',
          },
        },
        feedbacks: {
          endpoint: api.aiBridge.urlAdmin,
          credentials: aiBridgeCredentials,
          service: 'feedbacks',
        },
        strapi: {
          endpoint: api.aiBridge.urlAdmin,
          credentials: aiBridgeCredentials,
          headers: {
            'Content-Type': 'application/json',
          },
        },
        mcp_servers: {
          endpoint: api.aiBridge.urlAdmin,
          credentials: aiBridgeCredentials,
          service: 'mcp_servers',
        },
      }

      commit('set', { config })
    }
    commit('set', { globalLoading: false })
  },
}

export default {
  state: state(),
  getters,
  mutations,
  actions,
}
