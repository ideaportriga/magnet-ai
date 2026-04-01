import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * Pinia store for dashboard filter options.
 * Replaces Vuex ragDashboard, agentDashboard, and llmDashboard modules.
 */
export const useDashboardStore = defineStore('dashboard', () => {
  const ragDashboardOptions = ref<Record<string, any>>({})
  const agentDashboardOptions = ref<Record<string, any>>({})
  const llmDashboardOptions = ref<Record<string, any>>({})

  function setRagDashboardOptions(options: Record<string, any>) {
    ragDashboardOptions.value = options
  }
  function setAgentDashboardOptions(options: Record<string, any>) {
    agentDashboardOptions.value = options
  }
  function setLlmDashboardOptions(options: Record<string, any>) {
    llmDashboardOptions.value = options
  }

  return {
    ragDashboardOptions,
    agentDashboardOptions,
    llmDashboardOptions,
    setRagDashboardOptions,
    setAgentDashboardOptions,
    setLlmDashboardOptions,
  }
})
