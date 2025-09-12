import useMainStore from '@/pinia/modules/main'
import useAuth from '@/pinia/modules/auth'
import useSearch from '@/pinia/modules/search'
/** Entities */
import useAgents from '@/pinia/modules/entities/agents'
import useAiApps from '@/pinia/modules/ai_apps'
import useCollections from '@/pinia/modules/entities/collections'
import usePromptTemplates from '@/pinia/modules/entities/prompt_templates'
import useRagTools from '@/pinia/modules/entities/rag_tools'
import useRetrieval from '@/pinia/modules/entities/retrieval'
import useModel from '@/pinia/modules/entities/model'
//Tabs
import useAgentTab from '@/pinia/modules/agentTab'
import useChatCompletion from '@/pinia/modules/chatCompletion'

export {
  useMainStore,
  useAuth,
  useAgents,
  useAiApps,
  useCollections,
  usePromptTemplates,
  useRagTools,
  useRetrieval,
  useModel,
  useSearch,
  useAgentTab,
  useChatCompletion,
}
