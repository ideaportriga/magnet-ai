import _ from 'lodash'
import { fetchData } from '@shared'

const state = () => ({
  mcp_server: {},
  initialMcpServer: {},
  mcpSettingsEditMode: false,
})

const getters = {
  mcp_server: (state) => state.mcp_server,
  initialMcpServer: (state) => state.initialMcpServer,
  mcp_tool: (state) => (name: string) => {
    // if (!state.mcp_server.tools) return null
    return state.mcp_server?.tools?.find((tool) => tool.name === name)
  },
  isMcpServerChanged: (state) => {
    return !_.isEqual(state.mcp_server, state.initialMcpServer)
  },
  mcpSettingsEditMode: (state) => state.mcpSettingsEditMode,
}

const mutations = {
  setMcpServer(state, payload) {
    const server = _.cloneDeep(payload)
    if (server?.headers) server.headers = new Map(Object.entries(server.headers))
    // if (server.secrets) server.secrets = new Map(Object.entries(server.secrets))
    state.mcp_server = _.cloneDeep(server)
    state.initialMcpServer = _.cloneDeep(server)
  },
  updateMcpServerProperty(state, payload) {
    state.mcp_server[payload.key] = payload.value
  },
  updateNestedMcpServerProperty(state, { path, value }) {
    const keys = path.split('.')
    let target = state.mcp_server

    for (let i = 0; i < keys.length - 1; i++) {
      if (!(keys[i] in target) || target[keys[i]] === null) {
        target = target[keys[i]] = {}
      } else {
        target = target[keys[i]]
      }
    }
  },
  setInitMcpServer(state) {
    state.initialMcpServer = _.cloneDeep(state.mcp_server)
  },
  setTools(state, tools) {
    console.log('tools', tools)
    state.mcp_server.tools = tools
    state.initialMcpServer.tools = tools
  },
  removeMcpServerProperty(state, key) {
    delete state.mcp_server[key]
  },
  toggleMcpSettingsEditMode(state, value) {
    state.mcpSettingsEditMode = value
  },
}

const actions = {
  setMcpServer(context, payload) {
    context.commit('setMcpServer', payload)
  },
  updateMcpServerProperty(context, payload) {
    context.commit('updateMcpServerProperty', payload)
  },
  async testMcpServerConnection(context, payload) {
    try {
      const response = await fetchData({
        method: 'POST',
        service: `mcp_servers/${payload.id}/test`,
        credentials: 'include',
        body: JSON.stringify(payload),
        endpoint: context.state.config?.mcp_servers?.endpoint,
        headers: {
          'Content-Type': 'application/json',
        },
      })
      if (response.error) throw response
      return true
    } catch (error) {
      console.error(error)
      return false
    }
  },
  async saveMcpServer(context) {
    const mcpServer = _.cloneDeep(context.state.mcp_server)
    const id = mcpServer.id
    const entity = 'mcp_servers'
    delete mcpServer._metadata
    delete mcpServer.id
    delete mcpServer.secrets_names
    if (mcpServer.headers) mcpServer.headers = Object.fromEntries(mcpServer.headers)
    if (mcpServer.secrets) mcpServer.secrets = Object.fromEntries(mcpServer.secrets)
    await context.dispatch('chroma/update', { payload: { id, data: mcpServer }, entity }, { root: true })
    context.commit('setInitMcpServer')
    context.commit('toggleMcpSettingsEditMode', false)
  },
  async syncMcpTools(context) {
    try {
      const response = await fetchData({
        method: 'POST',
        service: `mcp_servers/${context.state.mcp_server.id}/sync_tools`,
        credentials: 'include',
        endpoint: context.state.config?.mcp_servers?.endpoint,
      })
      if (response.error) throw response
      const tools = await response.json()
      context.commit('setTools', tools)
      await context.dispatch('chroma/get', { entity: 'mcp_servers' }, { root: true })
      return true
    } catch (error) {
      console.error(error)
      return false
    }
  },
  async callMcpTool(context, payload) {
    const response = await fetchData({
      method: 'POST',
      service: `mcp_servers/${context.state.mcp_server.id}/tools/${payload.tool_name}/call`,
      credentials: 'include',
      body: JSON.stringify(payload.input),
      endpoint: context.state.config?.mcp_servers?.endpoint,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (response.error) {
      context.commit('set', {
        errorMessage: {
          technicalError: response?.error,
          text: `Error calling MCP tool`,
        },
      })
      return null
    }

    return response.json()
  },
  removeMcpServerProperty(context, key) {
    context.commit('removeMcpServerProperty', key)
  },
  toggleMcpSettingsEditMode(context, value) {
    if (!value) {
      context.commit('removeMcpServerProperty', 'secrets')
    } else {
      const secret_names = context.state.mcp_server.secrets_names
      const value = secret_names ? new Map(secret_names.map((key) => [key, ''])) : new Map([['', '']])
      context.commit('updateMcpServerProperty', {
        key: 'secrets',
        value: value,
      })
    }
    context.commit('toggleMcpSettingsEditMode', value)
  },
}

export default {
  namespaced: true,
  state: state(),
  getters,
  mutations,
  actions,
}
