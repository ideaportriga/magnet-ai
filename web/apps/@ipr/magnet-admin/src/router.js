import { createRouter, createWebHashHistory } from 'vue-router'
import ApplicationPage from '@/components/AIApps/Page.vue'
import ApplicationDetailsPage from '@/components/AIApps/details.vue'
import ApplicationDetailsTabsPage from '@/components/AIAppTabs/details.vue'
import PromptsPage from '@/components/Prompts/Page.vue'
import PromptsDetailPage from '@/components/Prompts/details.vue'
import ConfigurationPage from '@/components/Configuration/Page.vue'
import ConfigurationDetailPage from '@/components/Configuration/details.vue'
import CollectionsPage from '@/components/Collections/Page.vue'
import CollectionsDetailPage from '@/components/Collections/details.vue'
import CollectionItemsPage from '@/components/CollectionItems/Page.vue'
import { TracesPage, TracesDetailPage } from '@/components/Observability/Traces'
import EvaluationSetsPage from '@/components/EvaluationSets/Page.vue'
import EvaluationSetsDetailsPage from '@/components/EvaluationSets/details.vue'
import EvaluationJobsPage from '@/components/EvaluationJobs/Page.vue'
import EvaluationDetails from '@/components/EvaluationJobs/details.vue'
import RetrievalPage from '@/components/Retrieval/Page.vue'
import RetrievalDetailPage from '@/components/Retrieval/details.vue'
import ModelPage from '@/components/ModelConfig/Page.vue'
import ModelDetailPage from '@/components/ModelConfig/details.vue'
import AssistantToolsPage from '@/components/AssistantTools/Page.vue'
import AssistantToolsDetailPage from '@/components/AssistantTools/details.vue'
import EvaluationDetailsCompare from '@/components/EvaluationJobs/detailsCompare.vue'
import AgentsPage from '@/components/Agents/Page.vue'
import AgentsDetailPage from '@/components/Agents/details.vue'
import AgentsTopicDetailPage from '@/components/Agents/topicDetails.vue'
import AgentsTopicActionDetailPage from '@/components/Agents/actionDetails.vue'
import ApiToolsPage from '@/components/ApiTools/Page.vue'
import ApiToolsDetailPage from '@/components/ApiTools/details.vue'
import DashboardPage from '@/components/Dashboard/Page.vue'
import ConversationPage from '@/components/Conversation/Page.vue'
import JobsPage from '@/components/Jobs/Page.vue'
import McpPage from '@/components/Mcp/Page.vue'
import McpDetailsPage from '@/components/Mcp/Details.vue'
import McpToolsDetailPage from '@/components/Mcp/Tools.vue'
import ApiKeysPage from '@/components/ApiKeys/Page.vue'
import ApiServersPage from '@/components/ApiServers/Page.vue'
import ApiServersDetailsPage from '@/components/ApiServers/Details.vue'
import ModelProvidersPage from '@/components/ModelProviders/Page.vue'
import ModelProvidersDetails from '@/components/ModelProviders/Details.vue'
import KnowledgeProvidersPage from '@/components/KnowledgeProviders/Page.vue'
import KnowledgeProvidersDetails from '@/components/KnowledgeProviders/Details.vue'
import KnowledgeGraphPage from '@/components/KnowledgeGraph/Page.vue'
import store from '@/store/index'

const routes = [
  {
    path: '/',
    name: 'main',
    component: ApplicationPage,
    meta: {
      pageLabel: 'AI App',
    },
  },
  {
    path: '/ai-apps/:id/items/:tab',
    name: 'AIAppTabsDetail',
    component: ApplicationDetailsTabsPage,
    meta: {
      pageLabel: 'AI App',
      chroma: true,
      entity: 'ai_apps',
    },
  },
  {
    path: '/ai-apps/:id?',
    name: 'AIApp',
    component: ApplicationPage,
    meta: {
      pageLabel: 'AI App',
      chroma: true,
      entity: 'ai_apps',
    },
  },
  {
    path: '/ai-apps/:id',
    name: 'AIAppDetail',
    component: ApplicationDetailsPage,
    meta: {
      pageLabel: 'AI App',
      chroma: true,
      entity: 'ai_apps',
    },
  },
  {
    path: '/ai-apps',
    name: 'AI App',
    component: ApplicationPage,
    meta: {
      pageLabel: 'AI App',
      chroma: true,
      entity: 'ai_apps',
    },
  },
  {
    path: '/prompt-templates/:id?',
    name: 'PromptTemplates',
    component: PromptsPage,
    meta: {
      pageLabel: 'Prompt Templates',
    },
  },
  {
    path: '/prompt-templates/:id',
    name: 'PromptTemplatesItem',
    component: PromptsDetailPage,
    meta: {
      pageLabel: 'Prompt Templates',
      chroma: true,
      entity: 'promptTemplates',
    },
  },

  {
    path: '/knowledge-sources/:id/items/:chunk?',
    name: 'CollectionItems',
    component: CollectionItemsPage,
    meta: {
      pageLabel: 'Knowledge sources',
      chroma: true,
      entity: 'documents',
    },
  },
  {
    path: '/knowledge-sources/',
    name: 'Collections',
    component: CollectionsPage,
    meta: {
      pageLabel: 'Knowledge sources',
      //chroma: true,
      entity: 'collections',
    },
  },
  {
    path: '/knowledge-sources/:id',
    name: 'CollectionDetail',
    component: CollectionsDetailPage,
    meta: {
      pageLabel: 'Knowledge sources',
      chroma: true,
      entity: 'collections',
    },
  },
  {
    path: '/rag-tools/:id?',
    name: 'Configuration',
    component: ConfigurationPage,
    meta: {
      pageLabel: 'RAG Tools',
    },
  },
  {
    path: '/rag-tools/:id',
    name: 'ConfigurationItems',
    component: ConfigurationDetailPage,
    meta: {
      pageLabel: 'RAG Tools',
      chroma: true,
      entity: 'rag_tools',
    },
  },
  {
    path: '/retrieval/:id?',
    name: 'Retrieval',
    component: RetrievalPage,
    meta: {
      pageLabel: 'Retrieval Tools',
    },
  },
  {
    path: '/retrieval/:id',
    name: 'RetrievalItems',
    component: RetrievalDetailPage,
    meta: {
      pageLabel: 'Retrieval Tools',
      chroma: true,
      entity: 'retrieval',
    },
  },
  {
    path: '/model-providers',
    name: 'ModelProviders',
    component: ModelProvidersPage,
    meta: {
      pageLabel: 'Model Providers',
    },
  },
  {
    path: '/model-providers/:id',
    name: 'ModelProvidersDetails',
    component: ModelProvidersDetails,
    meta: {
      pageLabel: 'Model Providers',
      chroma: true,
      entity: 'provider',
    },
  },
  {
    path: '/model/:id?',
    name: 'Model',
    component: ModelPage,
    meta: {
      pageLabel: 'Models',
    },
  },
  {
    path: '/model/:id',
    name: 'ModelItems',
    component: ModelDetailPage,
    meta: {
      pageLabel: 'Models',
      chroma: true,
      entity: 'model',
    },
  },
  {
    path: '/observability-traces',
    name: 'ObservabilityTraces',
    component: TracesPage,
    meta: {
      pageLabel: 'Traces',
      chroma: true,
      entity: 'observability_traces',
    },
  },
  {
    path: '/observability-traces/:id',
    name: 'ObservabilityTracesDetail',
    component: TracesDetailPage,
    meta: {
      pageLabel: 'Traces',
      chroma: true,
      detail: true,
      entity: 'observability_traces',
    },
  },
  {
    path: '/evaluation-sets/',
    name: 'EvaluationSets',
    component: EvaluationSetsPage,
    meta: {
      pageLabel: 'Test Sets',
      //chroma: true,
      entity: 'evaluation_sets',
    },
  },
  {
    path: '/evaluation-sets/:id',
    name: 'EvaluationSetDetails',
    component: EvaluationSetsDetailsPage,
    meta: {
      pageLabel: 'Test Sets',
      chroma: true,
      entity: 'evaluation_sets',
    },
  },
  {
    path: '/evaluation-jobs/:id?',
    name: 'EvaluationEvaluationJobs',
    component: EvaluationJobsPage,
    meta: {
      pageLabel: 'Evaluations',
      chroma: true,
      entity: 'evaluation_jobs',
    },
  },
  {
    path: '/evaluation-jobs/:id',
    name: 'Evaluation',
    component: EvaluationDetails,
    meta: {
      pageLabel: 'Evaluations',
      chroma: true,
      entity: 'evaluation_jobs',
    },
  },
  {
    path: '/evaluation/compare',
    name: 'EvaluationCompare',
    component: EvaluationDetailsCompare,
    meta: {
      pageLabel: 'Evaluations',
      chroma: true,
      entity: 'evaluation_jobs',
    },
  },
  {
    path: '/assistant-tools/:id?',
    name: 'Assistant',
    component: AssistantToolsPage,
    meta: {
      pageLabel: 'Assistant Tools',
    },
  },
  {
    path: '/assistant-tools/:id',
    name: 'AssistantItems',
    component: AssistantToolsDetailPage,
    meta: {
      pageLabel: 'Assistant Tools',
      chroma: true,
      entity: 'assistant_tools',
    },
  },
  {
    path: '/api-tools',
    name: 'ApiTools',
    component: ApiToolsPage,
  },
  // {
  //   path: '/usage',
  //   name: 'Usage',
  //   component: DashboardPage,
  //   meta: {
  //     pageLabel: 'Usage',
  //   },
  // },
  {
    path: '/usage',
    redirect: '/usage/rag',
  },
  {
    path: '/usage/:tab',
    name: 'Usage',
    component: DashboardPage,
    meta: {
      pageLabel: 'Usage',
    },
  },
  // Agents listing
  {
    path: '/agents/:id?',
    name: 'Agents',
    component: AgentsPage,
    meta: {
      pageLabel: 'Agents',
      chroma: true,
      entity: 'agents',
    },
  },
  // Agent detail (parent)
  {
    path: '/agents/:id',
    name: 'AgentDetail',
    component: AgentsDetailPage,
    meta: {
      pageLabel: 'Agent',
      chroma: true,
      entity: 'agents',
    },
    children: [
      // Child routes under AgentDetail
      {
        path: 'topics/:topicId',
        name: 'AgentTopicDetail',
        component: AgentsTopicDetailPage,
        meta: {
          pageLabel: 'Agent',
          chroma: true,
          entity: 'agents',
        },
      },
      {
        path: 'topics/:topicId/actions/:actionId',
        name: 'AgentTopicActionDetail',
        component: AgentsTopicActionDetailPage,
        meta: {
          pageLabel: 'Agent',
          chroma: true,
          entity: 'agents',
        },
      },
    ],
  },
  {
    path: '/jobs',
    name: 'Jobs',
    component: JobsPage,
    meta: {
      pageLabel: 'Jobs',
      chroma: true,
      entity: 'jobs',
    },
  },
  {
    path: '/conversation/:id?',
    name: 'Conversation',
    component: ConversationPage,
    meta: {
      pageLabel: 'Conversation',
    },
  },
  {
    path: '/mcp',
    name: 'Mcp',
    component: McpPage,
    meta: {
      pageLabel: 'MCP Servers',
    },
  },
  {
    path: '/mcp/:id',
    name: 'McpDetail',
    component: McpDetailsPage,
    meta: {
      pageLabel: 'MCP Servers',
      chroma: true,
      entity: 'mcp_servers',
    },
  },
  {
    path: '/mcp/:id/tools/:name',
    name: 'McpToolsDetail',
    component: McpToolsDetailPage,
    meta: {
      pageLabel: 'MCP Tools',
    },
  },
  {
    path: '/api-keys',
    name: 'ApiKeys',
    component: ApiKeysPage,
    meta: {
      pageLabel: 'API Keys',
    },
  },
  {
    path: '/api-servers',
    name: 'ApiServers',
    component: ApiServersPage,
    meta: {
      pageLabel: 'API Servers',
      chroma: true,
      entity: 'api_servers',
    },
  },
  {
    path: '/api-servers/:id',
    name: 'ApiServersDetail',
    component: ApiServersDetailsPage,
    meta: {
      pageLabel: 'API Server',
      chroma: true,
      entity: 'api_servers',
    },
  },
  {
    path: '/api-servers/:id/tools/:name',
    name: 'ApiToolsDetails',
    component: ApiToolsDetailPage,
    meta: {
      pageLabel: 'API Server',
      chroma: true,
      entity: 'api_servers',
    },
  },
  {
    path: '/knowledge-providers',
    name: 'KnowledgeProviders',
    component: KnowledgeProvidersPage,
    meta: {
      pageLabel: 'Knowledge Source Providers',
    },
  },
  {
    path: '/knowledge-providers/:id',
    name: 'KnowledgeProvidersDetails',
    component: KnowledgeProvidersDetails,
    meta: {
      pageLabel: 'Knowledge Source Providers',
      chroma: true,
      entity: 'provider',
    },
  },
  {
    path: '/knowledge-graph',
    name: 'KnowledgeGraph',
    component: KnowledgeGraphPage,
    meta: {
      pageLabel: 'Knowledge Graph',
    },
  },
  {
    path: '/knowledge-graph/:id',
    name: 'KnowledgeGraphDetail',
    component: () => import('@/components/KnowledgeGraph/Details.vue'),
    meta: {
      pageLabel: 'Knowledge Graph',
      chroma: true,
      entity: 'knowledge_graph',
    },
  },
  {
    path: '/knowledge-graph/:id/documents/:documentId',
    name: 'KnowledgeGraphDocumentDetail',
    component: () => import('@/components/KnowledgeGraph/DataExplorer/DocumentDetails.vue'),
    meta: {
      pageLabel: 'Knowledge Graph',
      chroma: true,
      entity: 'knowledge_graph',
      detail: true,
    },
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  if (store.getters.showLeaveConfirm) {
    store.commit('setIsNavigationCancelled', false)
    next()
  }

  if (
    (from.name === 'ModelItems' && store.getters['modelConfig/isEntityChanged']) ||
    (from.name === 'ConfigurationItems' && store.getters.isRagChanged) ||
    (from.name === 'RetrievalItems' && store.getters.isRetrievalChanged) ||
    (from.name === 'EvaluationSetDetails' && store.getters.isEvaluationSetChanged) ||
    (from.name === 'PromptTemplatesItem' && store.getters.isPromptTemplateChanged) ||
    ((from.name === 'AIAppDetail' || from.name === 'AIAppTabsDetail') &&
      store.getters.isAIAppChanged &&
      to.name !== 'AIAppDetail' &&
      to.name !== 'AIAppTabsDetail') ||
    (from.name === 'ApiToolsDetails' && store.getters.isApiToolChanged) ||
    ((from.name === 'AgentDetail' || from.name === 'AgentTopicDetail' || from.name === 'AgentTopicActionDetail') &&
      store.getters.isAgentDetailChanged &&
      to.name !== 'AgentDetail' &&
      to.name !== 'AgentTopicDetail' &&
      to.name !== 'AgentTopicActionDetail') ||
    (from.name === 'McpDetail' && store.getters.isMcpServerChanged) ||
    (from.name === 'ApiServersDetail' && store.getters.isApiServerChanged) ||
    (from.name === 'ApiToolsDetails' && store.getters.isApiServerChanged) ||
    (from.name === 'ModelProvidersDetails' && store.getters.isProviderChanged) ||
    (from.name === 'KnowledgeProvidersDetails' && store.getters.isProviderChanged)
  ) {
    store.commit('setNextRoute', to.fullPath)
    store.commit('showPopup')
    store.commit('setIsNavigationCancelled', true)
    next(false)
  } else {
    store.commit('setIsNavigationCancelled', false)
    next()
  }
})

router.afterEach(async (to) => {
  if (store.getters.isNavigationCancelled) {
    return
  }

  const query = to.query ?? {}

  store.commit('set', {
    ...(query.sourceSystem ? { sourceSystem: query.sourceSystem } : {}),
    ...(query.viewMode ? { viewMode: query.viewMode } : {}),
    ...(query.agentRecordId ? { agentRecordId: query.agentRecordId } : {}),
    ...(query.agentObjectType ? { agentObjectType: query.agentObjectType } : {}),
    ...(query.sourceSystemUserName ? { sourceSystemUserName: query.sourceSystemUserName } : {}),
  })

  if (to.meta.chroma) {
    console.log('after each', to)
    store.dispatch(`chroma/selectFromRouter`, { payload: to.params, entity: to.meta.entity, detail: to.meta?.detail })
    if (to.meta.entity === 'observability_traces') {
      store.dispatch(`chroma/reset`, { entity: to.meta.entity })
    }
  }

  if (to.meta.templates) {
    console.log('after each', to)
    store.dispatch(`strapi/selectFromRouter`, { payload: to.params, entity: to.meta.entity })
  }

  if (to.meta.prompts) {
    console.log('after each', to)
    store.dispatch('selectPromptFromRouter', { payload: to.params })
  }
})

export default router
