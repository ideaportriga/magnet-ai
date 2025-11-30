import _ from 'lodash'
import { fetchData } from '@shared'

const state = () => ({
  api_server: {},
  initialApiServer: {},
  apiSettingsEditMode: false,
  apiSettingsSecretsEditMode: false,
})

const getters = {
  api_server: (state) => state.api_server,
  initialApiServer: (state) => state.initialApiServer,
  isApiServerChanged: (state) => {
    return !_.isEqual(state.api_server, state.initialApiServer)
  },
  apiSettingsEditMode: (state) => state.apiSettingsEditMode,
  apiSettingsSecretsEditMode: (state) => state.apiSettingsSecretsEditMode,
  toolByName: (state) => (name) => {
    return state.api_server.tools?.find((tool) => tool.system_name === name)
  },
  originalApiSecrets: (state) => {
    const secrets = state.initialApiServer.secrets_encrypted
    if (!secrets) return []
    if (secrets instanceof Map) {
      return Array.from(secrets.keys())
    }
    return Object.keys(secrets)
  },
}

const mutations = {
  setApiServer(state, payload) {
    const server = _.cloneDeep(payload)
    if (server?.security_values) server.security_values = new Map(Object.entries(server.security_values))
    if (server?.secrets_encrypted) server.secrets_encrypted = new Map(Object.entries(server.secrets_encrypted))
    state.api_server = _.cloneDeep(server)
    state.initialApiServer = _.cloneDeep(server)
  },
  updateApiServerProperty(state, payload) {
    state.api_server[payload.key] = payload.value
  },
  updateNestedApiServerProperty(state, { path, value }) {
    const keys = path.split('.')
    let target = state.api_server

    for (let i = 0; i < keys.length - 1; i++) {
      if (!(keys[i] in target) || target[keys[i]] === null) {
        target = target[keys[i]] = {}
      } else {
        target = target[keys[i]]
      }
    }
  },
  setInitApiServer(state) {
    state.initialApiServer = _.cloneDeep(state.api_server)
  },
  removeApiServerProperty(state, key) {
    delete state.api_server[key]
  },
  toggleApiSettingsSecretsEditMode(state, value) {
    state.apiSettingsSecretsEditMode = value
  },
  setNestedApiServerProperty(state, { system_name, path, value }) {
    const keys = path.split('.')
    const tools = state.api_server.tools || []
    let target = tools.find((tool) => tool.system_name === system_name)

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
  },
  toggleApiSettingsEditMode(state, value) {
    state.apiSettingsEditMode = value
  },
  matchTools(state, payload) {
    console.log('MATCH TOOLS', payload)
    state.api_server.tools = payload
    state.initialApiServer.tools = payload
  },
}

const actions = {
  setApiServer(context, payload) {
    context.commit('setApiServer', payload)
  },
  setApiServerById(context, id) {
    const server = context.getters.chroma.api_servers.items.find((item) => item.id === id)
    context.commit('setApiServer', server)
  },
  matchTools(context, payload) {
    const tools = context.getters.chroma.api_servers.items.find((item) => item.id === context.state.api_server.id)?.tools || []
    context.commit('matchTools', tools)
  },
  updateApiServerProperty(context, payload) {
    context.commit('updateApiServerProperty', payload)
  },
  async saveApiServer(context) {
    const apiServer = _.cloneDeep(context.state.api_server)
    const id = apiServer.id
    const entity = 'api_servers'
    delete apiServer._metadata
    delete apiServer.id
    delete apiServer.secrets_names
    if (apiServer.security_values) {
      apiServer.security_values = apiServer.security_values instanceof Map ? Object.fromEntries(apiServer.security_values) : apiServer.security_values
    }
    if (apiServer.secrets_encrypted) {
      apiServer.secrets_encrypted =
        apiServer.secrets_encrypted instanceof Map ? Object.fromEntries(apiServer.secrets_encrypted) : apiServer.secrets_encrypted
    }
    await context.dispatch('chroma/update', { payload: { id, data: apiServer }, entity }, { root: true })
    context.commit('setInitApiServer')
    context.commit('toggleApiSettingsSecretsEditMode', false)
    context.commit('toggleApiSettingsEditMode', false)
  },
  removeApiServerProperty(context, key) {
    context.commit('removeApiServerProperty', key)
  },
  toggleApiSettingsSecretsEditMode(context, value) {
    if (!value) {
      context.commit('removeApiServerProperty', 'secrets_encrypted')
    } else {
      const secret_names = context.state.api_server.secrets_names
      const value = secret_names ? new Map(secret_names.map((key) => [key, ''])) : new Map([['', '']])
      context.commit('updateApiServerProperty', {
        key: 'secrets_encrypted',
        value: value,
      })
    }
    context.commit('toggleApiSettingsSecretsEditMode', value)
  },
  async specFromText(context, payload) {
    try {
      const response = await fetchData({
        endpoint: context.state.config?.api?.aiBridge?.urlAdmin, // context.state.config?.collections?.endpoint,
        service: 'api_servers/parse_openapi_spec_text',
        method: 'POST',
        credentials: 'include',
        body: JSON.stringify({
          spec: payload,
        }),
      })
      if (response.error) {
        throw response.error
      }
      return response.json()
    } catch (error) {
      context.commit('set', { errorMessage: { technicalError: error, text: 'Error parsing OpenAPI spec' } }, { root: true })
      throw error
    }
  },

  async addTools(context, payload) {
    const currentTools = context.state.api_server.tools || []
    currentTools.push(...payload)
    const response = await context.dispatch('updateTools', currentTools)
    return response
  },
  async updateTools(context, payload) {
    const id = context.state.api_server.id
    const response = await fetchData({
      endpoint: context.state.config?.api?.aiBridge?.urlAdmin, // context.state.config?.collections?.endpoint,
      service: `api_servers/${id}`,
      method: 'PATCH',
      credentials: 'include',
      body: JSON.stringify({
        tools: payload,
      }),
    })
    context.commit('matchTools', payload)
    return response.json()
  },
  setNestedApiServerProperty(context, { path, value }) {
    context.commit('setNestedApiServerProperty', { path, value })
  },
  async testServerApiTool(context, payload) {
    try {
      const response = await fetchData({
        endpoint: context.state.config?.api?.aiBridge?.urlAdmin, // context.state.config?.collections?.endpoint,
        service: 'api_servers/call_tool',
        method: 'POST',
        credentials: 'include',
        body: JSON.stringify({
          server: context.state.api_server.system_name,
          tool: payload.tool,
          input_params: payload.input_params,
          variables: payload.variables,
        }),
      })
      if (response.error) {
        throw response.error.message
      }
      const res = await response.json()
      return res.content
    } catch (error) {
      context.commit('set', { errorMessage: { technicalError: error, text: 'Error testing server API tool' } }, { root: true })
      throw error
    }
  },
}

export default {
  namespaced: true,
  state: state(),
  getters,
  mutations,
  actions,
}
