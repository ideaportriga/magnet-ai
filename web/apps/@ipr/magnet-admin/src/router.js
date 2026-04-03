import { createRouter, createWebHashHistory } from 'vue-router'
import { usePopupStore } from '@/stores/popupStore'
import { useEditBufferStore } from '@/stores/editBufferStore'
import { useKnowledgeGraphPageStore } from '@/stores/entityDetailStores'
import { ROUTE_ENTITY_TO_BUFFER_TYPE } from '@/constants/entityMapping'

// Entity label map for workspace tabs
const entityLabelMap = {
  provider: 'Model Provider',
  model: 'Model',
  agents: 'Agent',
  ai_apps: 'AI App',
  promptTemplates: 'Prompt Template',
  rag_tools: 'RAG Tool',
  retrieval: 'Retrieval Tool',
  collections: 'Knowledge Source',
  evaluation_sets: 'Test Set',
  evaluation_jobs: 'Evaluation',
  assistant_tools: 'Assistant Tool',
  api_servers: 'API Server',
  mcp_servers: 'MCP Server',
  knowledge_graph: 'Knowledge Graph',
  observability_traces: 'Trace',
}

const routes = [
  {
    path: '/',
    name: 'main',
    component: () => import('@/components/AIApps/Page.vue'),
    meta: {
      pageLabel: 'AI App',
    },
  },
  {
    path: '/ai-apps/:id/items/:tab',
    name: 'AIAppTabsDetail',
    component: () => import('@/components/AIAppTabs/details.vue'),
    meta: {
      pageLabel: 'AI App',
      chroma: true,
      entity: 'ai_apps',
      headerComponent: 'ai-apps-header',
    },
  },
  {
    path: '/ai-apps/:id?',
    name: 'AIApp',
    component: () => import('@/components/AIApps/Page.vue'),
    meta: {
      pageLabel: 'AI App',
      chroma: true,
      entity: 'ai_apps',
    },
  },
  {
    path: '/ai-apps/:id',
    name: 'AIAppDetail',
    component: () => import('@/components/AIApps/details.vue'),
    meta: {
      pageLabel: 'AI App',
      chroma: true,
      entity: 'ai_apps',
      headerComponent: 'ai-apps-header',
    },
  },
  {
    path: '/ai-apps',
    name: 'AI App',
    component: () => import('@/components/AIApps/Page.vue'),
    meta: {
      pageLabel: 'AI App',
      chroma: true,
      entity: 'ai_apps',
    },
  },
  {
    path: '/prompt-templates/:id?',
    name: 'PromptTemplates',
    component: () => import('@/components/Prompts/Page.vue'),
    meta: {
      pageLabel: 'Prompt Templates',
    },
  },
  {
    path: '/prompt-templates/:id',
    name: 'PromptTemplatesItem',
    component: () => import('@/components/Prompts/details.vue'),
    meta: {
      pageLabel: 'Prompt Templates',
      chroma: true,
      entity: 'promptTemplates',
      headerComponent: 'prompts-header',
    },
  },

  {
    path: '/knowledge-sources/:id/items/:chunk?',
    name: 'CollectionItems',
    component: () => import('@/components/CollectionItems/Page.vue'),
    meta: {
      pageLabel: 'Knowledge sources',
      chroma: true,
      entity: 'documents',
      headerComponent: 'collections-header',
    },
  },
  {
    path: '/knowledge-sources/',
    name: 'Collections',
    component: () => import('@/components/Collections/Page.vue'),
    meta: {
      pageLabel: 'Knowledge sources',
      //chroma: true,
      entity: 'collections',
    },
  },
  {
    path: '/knowledge-sources/:id',
    name: 'CollectionDetail',
    component: () => import('@/components/Collections/details.vue'),
    meta: {
      pageLabel: 'Knowledge sources',
      chroma: true,
      entity: 'collections',
      headerComponent: 'collections-header',
    },
  },
  {
    path: '/rag-tools/:id?',
    name: 'Configuration',
    component: () => import('@/components/Configuration/Page.vue'),
    meta: {
      pageLabel: 'RAG Tools',
    },
  },
  {
    path: '/rag-tools/:id',
    name: 'ConfigurationItems',
    component: () => import('@/components/Configuration/details.vue'),
    meta: {
      pageLabel: 'RAG Tools',
      chroma: true,
      entity: 'rag_tools',
      headerComponent: 'configuration-header',
    },
  },
  {
    path: '/retrieval/:id?',
    name: 'Retrieval',
    component: () => import('@/components/Retrieval/Page.vue'),
    meta: {
      pageLabel: 'Retrieval Tools',
    },
  },
  {
    path: '/retrieval/:id',
    name: 'RetrievalItems',
    component: () => import('@/components/Retrieval/details.vue'),
    meta: {
      pageLabel: 'Retrieval Tools',
      chroma: true,
      entity: 'retrieval',
      headerComponent: 'retrieval-header',
    },
  },
  {
    path: '/deep-research/configs',
    name: 'DeepResearchConfigs',
    component: () => import('@/components/DeepResearch/Configs/Page.vue'),
    meta: {
      pageLabel: 'Deep Research Configs',
    },
  },
  {
    path: '/deep-research/runs',
    name: 'DeepResearchRuns',
    component: () => import('@/components/DeepResearch/Runs/Page.vue'),
    meta: {
      pageLabel: 'Deep Research Runs',
    },
  },
  {
    path: '/deep-research/configs/:id',
    name: 'DeepResearchDetails',
    component: () => import('@/components/DeepResearch/Configs/Details.vue'),
    meta: {
      pageLabel: 'Deep Research Config',
      headerComponent: 'deep-research-configs-header',
    },
  },
  {
    path: '/deep-research/runs/:id',
    name: 'DeepResearchRunDetails',
    component: () => import('@/components/DeepResearch/Runs/Details.vue'),
    meta: {
      pageLabel: 'Deep Research Run',
    },
  },
  {
    path: '/model-providers',
    name: 'ModelProviders',
    component: () => import('@/components/ModelProviders/Page.vue'),
    meta: {
      pageLabel: 'Model Providers',
    },
  },
  {
    path: '/model-providers/:id',
    name: 'ModelProvidersDetails',
    component: () => import('@/components/ModelProviders/Details.vue'),
    meta: {
      pageLabel: 'Model Providers',
      chroma: true,
      entity: 'provider',
      headerComponent: 'model-providers-header',
    },
  },
  {
    path: '/model/:id?',
    name: 'Model',
    component: () => import('@/components/ModelConfig/Page.vue'),
    meta: {
      pageLabel: 'Models',
    },
  },
  {
    path: '/model/:id',
    name: 'ModelItems',
    component: () => import('@/components/ModelConfig/details.vue'),
    meta: {
      pageLabel: 'Models',
      chroma: true,
      entity: 'model',
      headerComponent: 'model-config-header',
    },
  },
  {
    path: '/observability-traces',
    name: 'ObservabilityTraces',
    component: () => import('@/components/Observability/Traces/Page.vue'),
    meta: {
      pageLabel: 'Traces',
      chroma: true,
      entity: 'observability_traces',
    },
  },
  {
    path: '/observability-traces/:id',
    name: 'ObservabilityTracesDetail',
    component: () => import('@/components/Observability/Traces/details.vue'),
    meta: {
      pageLabel: 'Traces',
      chroma: true,
      detail: true,
      entity: 'observability_traces',
      headerComponent: 'observability-traces-header',
    },
  },
  {
    path: '/evaluation-sets/',
    name: 'EvaluationSets',
    component: () => import('@/components/EvaluationSets/Page.vue'),
    meta: {
      pageLabel: 'Test Sets',
      //chroma: true,
      entity: 'evaluation_sets',
    },
  },
  {
    path: '/evaluation-sets/:id',
    name: 'EvaluationSetDetails',
    component: () => import('@/components/EvaluationSets/details.vue'),
    meta: {
      pageLabel: 'Test Sets',
      chroma: true,
      entity: 'evaluation_sets',
      headerComponent: 'evaluation-sets-header',
    },
  },
  {
    path: '/evaluation-jobs/:id?',
    name: 'EvaluationEvaluationJobs',
    component: () => import('@/components/EvaluationJobs/Page.vue'),
    meta: {
      pageLabel: 'Evaluations',
      chroma: true,
      entity: 'evaluation_jobs',
    },
  },
  {
    path: '/evaluation-jobs/:id',
    name: 'Evaluation',
    component: () => import('@/components/EvaluationJobs/details.vue'),
    meta: {
      pageLabel: 'Evaluations',
      chroma: true,
      entity: 'evaluation_jobs',
    },
  },
  {
    path: '/evaluation/compare',
    name: 'EvaluationCompare',
    component: () => import('@/components/EvaluationJobs/detailsCompare.vue'),
    meta: {
      pageLabel: 'Evaluations',
      chroma: true,
      entity: 'evaluation_jobs',
    },
  },
  {
    path: '/assistant-tools/:id?',
    name: 'Assistant',
    component: () => import('@/components/AssistantTools/Page.vue'),
    meta: {
      pageLabel: 'Assistant Tools',
    },
  },
  {
    path: '/assistant-tools/:id',
    name: 'AssistantItems',
    component: () => import('@/components/AssistantTools/details.vue'),
    meta: {
      pageLabel: 'Assistant Tools',
      chroma: true,
      entity: 'assistant_tools',
      headerComponent: 'assistant-tools-header',
    },
  },
  {
    path: '/usage',
    redirect: '/usage/rag',
  },
  {
    path: '/usage/:tab',
    name: 'Usage',
    component: () => import('@/components/Dashboard/Page.vue'),
    meta: {
      pageLabel: 'Usage',
    },
  },
  // Agents listing
  {
    path: '/agents/:id?',
    name: 'Agents',
    component: () => import('@/components/Agents/Page.vue'),
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
    component: () => import('@/components/Agents/details.vue'),
    meta: {
      pageLabel: 'Agent',
      chroma: true,
      entity: 'agents',
      headerComponent: 'agents-header',
    },
    children: [
      // Child routes under AgentDetail
      {
        path: 'topics/:topicId',
        name: 'AgentTopicDetail',
        component: () => import('@/components/Agents/topicDetails.vue'),
        meta: {
          pageLabel: 'Agent',
          chroma: true,
          entity: 'agents',
          headerComponent: 'agents-header',
        },
      },
      {
        path: 'topics/:topicId/actions/:actionId',
        name: 'AgentTopicActionDetail',
        component: () => import('@/components/Agents/actionDetails.vue'),
        meta: {
          pageLabel: 'Agent',
          chroma: true,
          entity: 'agents',
          headerComponent: 'agents-header',
        },
      },
    ],
  },
  {
    path: '/jobs',
    name: 'Jobs',
    component: () => import('@/components/Jobs/Page.vue'),
    meta: {
      pageLabel: 'Jobs',
      chroma: true,
      entity: 'jobs',
    },
  },
  {
    path: '/files',
    name: 'Files',
    component: () => import('@/components/Files/Page.vue'),
    meta: {
      pageLabel: 'File Storage',
    },
  },
  {
    path: '/conversation/:id?',
    name: 'Conversation',
    component: () => import('@/components/Conversation/Page.vue'),
    meta: {
      pageLabel: 'Conversation',
      headerComponent: 'conversation-header',
    },
  },
  {
    path: '/mcp',
    name: 'Mcp',
    component: () => import('@/components/Mcp/Page.vue'),
    meta: {
      pageLabel: 'MCP Servers',
    },
  },
  {
    path: '/mcp/:id',
    name: 'McpDetail',
    component: () => import('@/components/Mcp/Details.vue'),
    meta: {
      pageLabel: 'MCP Servers',
      chroma: true,
      entity: 'mcp_servers',
      headerComponent: 'mcp-header',
    },
  },
  {
    path: '/mcp/:id/tools/:name',
    name: 'McpToolsDetail',
    component: () => import('@/components/Mcp/Tools.vue'),
    meta: {
      pageLabel: 'MCP Servers',
      chroma: true,
      entity: 'mcp_servers',
      headerComponent: 'mcp-header',
    },
  },
  {
    path: '/api-keys',
    name: 'ApiKeys',
    component: () => import('@/components/ApiKeys/Page.vue'),
    meta: {
      pageLabel: 'API Keys',
    },
  },
  {
    path: '/api-servers',
    name: 'ApiServers',
    component: () => import('@/components/ApiServers/Page.vue'),
    meta: {
      pageLabel: 'API Servers',
      chroma: true,
      entity: 'api_servers',
    },
  },
  {
    path: '/api-servers/:id',
    name: 'ApiServersDetail',
    component: () => import('@/components/ApiServers/Details.vue'),
    meta: {
      pageLabel: 'API Server',
      chroma: true,
      entity: 'api_servers',
      headerComponent: 'api-servers-header',
    },
  },
  {
    path: '/api-servers/:id/tools/:name',
    name: 'ApiToolsDetails',
    component: () => import('@/components/ApiTools/details.vue'),
    meta: {
      pageLabel: 'API Server',
      chroma: true,
      entity: 'api_servers',
      headerComponent: 'api-servers-header',
    },
  },
  {
    path: '/knowledge-providers',
    name: 'KnowledgeProviders',
    component: () => import('@/components/KnowledgeProviders/Page.vue'),
    meta: {
      pageLabel: 'Knowledge Source Providers',
    },
  },
  {
    path: '/knowledge-providers/:id',
    name: 'KnowledgeProvidersDetails',
    component: () => import('@/components/KnowledgeProviders/Details.vue'),
    meta: {
      pageLabel: 'Knowledge Source Providers',
      chroma: true,
      entity: 'provider',
      headerComponent: 'knowledge-providers-header',
    },
  },
  {
    path: '/knowledge-graph',
    name: 'KnowledgeGraph',
    component: () => import('@/components/KnowledgeGraph/Page.vue'),
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
      headerComponent: 'knowledge-graph-header',
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
      headerComponent: 'knowledge-graph-header',
    },
  },
  {
    path: '/settings',
    redirect: '/settings/import',
  },
  {
    path: '/settings/:tab',
    name: 'Settings',
    component: () => import('@/components/Settings/Page.vue'),
    meta: {
      pageLabel: 'Settings',
    },
  },
  {
    path: '/prompt-queue',
    name: 'PromptQueue',
    component: () => import('@/components/PromptQueue/Page.vue'),
    meta: {
      pageLabel: 'Prompt Queue',
    },
  },
  {
    path: '/prompt-queue/:id',
    name: 'PromptQueueDetails',
    component: () => import('@/components/PromptQueue/Details.vue'),
    meta: {
      pageLabel: 'Prompt Queue',
      headerComponent: 'prompt-queue-header',
    },
  },
  {
    path: '/note-taker',
    name: 'NoteTakerConfigs',
    component: () => import('@/components/NoteTaker/Page.vue'),
    meta: {
      pageLabel: 'Note Taker',
    },
  },
  {
    path: '/note-taker/:id',
    name: 'NoteTakerSettings',
    component: () => import('@/components/NoteTaker/details.vue'),
    meta: {
      pageLabel: 'Note Taker',
      chroma: true,
      entity: 'note_taker',
      headerComponent: 'note-taker-header',
    },
  },
  {
    path: '/profile/:tab?',
    name: 'profile',
    component: () => import('@/components/Profile/ProfilePage.vue'),
    meta: {
      pageLabel: 'Profile',
    },
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

// Route names that share the same entity and allow internal navigation without dirty-check
const INTERNAL_NAV_GROUPS = {
  ai_apps: ['AIAppDetail', 'AIAppTabsDetail'],
  agents: ['AgentDetail', 'AgentTopicDetail', 'AgentTopicActionDetail'],
}

router.beforeEach((to, from, next) => {
  const popupStore = usePopupStore()

  if (popupStore.showLeaveConfirm) {
    popupStore.setIsNavigationCancelled(false)
    return next()
  }

  const editBuffer = useEditBufferStore()
  const entityType = from.meta?.entity

  // Check if navigating internally within the same entity group (e.g. agent tabs)
  const navGroup = entityType ? INTERNAL_NAV_GROUPS[entityType] : null
  if (navGroup && navGroup.includes(from.name) && navGroup.includes(to.name)) {
    popupStore.setIsNavigationCancelled(false)
    return next()
  }

  // Check editBuffer for unsaved changes
  let hasUnsavedChanges = false
  if (entityType && entityType !== 'knowledge_graph') {
    const bufferType = ROUTE_ENTITY_TO_BUFFER_TYPE[entityType]
    if (bufferType) {
      hasUnsavedChanges = editBuffer.isEntityTypeDirty(bufferType)
    }
  }

  // Special case: knowledge_graph uses its own store
  if (entityType === 'knowledge_graph') {
    try { hasUnsavedChanges = useKnowledgeGraphPageStore().isRetrievalChanged } catch { /* not initialized */ }
  }

  if (hasUnsavedChanges) {
    popupStore.setNextRoute(to.fullPath)
    popupStore.showPopup()
    popupStore.setIsNavigationCancelled(true)
    next(false)
  } else {
    popupStore.setIsNavigationCancelled(false)
    next()
  }
})

router.afterEach(async (to) => {
  const popupStore = usePopupStore()
  if (popupStore.isNavigationCancelled) {
    return
  }

  const query = to.query ?? {}

  // Query params are now read directly from route where needed

  // Open workspace tab for detail pages (routes with :id param and entity meta)
  if (to.params.id && to.meta.entity && to.meta.headerComponent) {
    try {
      const { useWorkspaceStore } = await import('@/stores/workspaceStore')
      const workspace = useWorkspaceStore()
      const entityType = to.meta.entity
      const entityId = to.params.id
      const typeLabel = entityLabelMap[entityType] || entityType

      // Try to get entity name from TanStack Query cache or entity-specific store
      let entityName = ''
      try {
        if (entityType === 'note_taker') {
          const { useNoteTakerStore } = await import('@/stores/noteTakerStore')
          const ntStore = useNoteTakerStore()
          entityName = ntStore.activeRecord?.name || ''
        } else {
          const { getCachedCatalog } = await import('@/queries/useCatalogOptions')
          const catalogItems = getCachedCatalog(entityType)
          const entity = catalogItems.find((i) => i.id === entityId)
          if (entity) {
            entityName = entity.name || entity.system_name || ''
          }
        }
      } catch {
        // ignore
      }

      const label = entityName || `${entityId.slice(0, 8)}...`
      workspace.openTab(entityType, entityId, label)
    } catch {
      // workspace store not initialized yet — ignore
    }
  }

  // Update browser tab title
  const pageLabel = to.meta?.pageLabel || 'Magnet AI'
  document.title = to.params.id ? `${pageLabel} — Magnet AI` : `${pageLabel} — Magnet AI`

})

export default router
