import { createStore } from 'vuex'
import createPersistedState from 'vuex-persistedstate'
import { mergeModules } from './utils'
import main from './modules/main'
import common from './modules/dataSources/common'
import search from './modules/search'
import prompts from './modules/prompts'
import wrappers from './modules/wrappers'
import strapi from './modules/dataSources/strapi'
import chroma from './modules/dataSources/chroma'
import rag from './modules/rag'
import knowledge from './modules/knowledge'
import ai_apps from './modules/ai_apps'
import evaluation_set from './modules/evaluation_set'
import customAppTabs from './modules/custom_app_tabs'
import retrieval from './modules/retrieval'
import popup from './modules/popup'
import modelConfig from './modules/model'
import evaluation from './modules/evaluation'
import assistantChat from './modules/dataSources/assistantChat'
import assistant_tools from './modules/assistant_tools'
import agentDetail from './modules/agentDetail'
import trace from './modules/trace'
import user from './modules/user'
import create from './modules/create'
import scheduler from './modules/scheduler'
import ragDashboard from './modules/ragDashboard'
import agentDashboard from './modules/agentDashboard'
import llmDashboard from './modules/llmDashboard'
import conversation from './modules/conversation'
import mcp_server from './modules/mcp_server'
import api_servers from './modules/api_servers'
import providers from './modules/providers'

const merged = mergeModules([
  main,
  common,
  search,
  prompts,
  wrappers,
  rag,
  knowledge,
  ai_apps,
  evaluation_set,
  customAppTabs,
  retrieval,
  popup,
  evaluation,
  assistant_tools,
  trace,
  agentDetail,
  user,
  create,
  scheduler,
  ragDashboard,
  agentDashboard,
  llmDashboard,
  conversation,
  mcp_server,
  api_servers,
  providers,
])

export default createStore({
  modules: {
    global: merged,
    chroma,
    strapi,
    modelConfig,
    assistantChat,
  },

  plugins: [
    createPersistedState({
      key: 'persistedStateKey',
      paths: ['chroma.collections.publicSelected', 'global.conversationRecords'],
    }),
  ],
})
