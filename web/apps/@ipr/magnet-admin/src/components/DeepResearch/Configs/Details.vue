<template>
  <div v-if="loading" class="cluster overflow-hidden full-height" data-wrap="no" style="min-inline-size: 1200px">
    <km-inner-loading :showing="loading" />
  </div>
  <div v-else class="stack overflow-hidden full-height" data-gap="0">
    <div class="mx-auto full-width stack full-height px-md" style="max-inline-size: 1200px; min-inline-size: 600px">
      <div class="cluster full-width mt-lg mb-sm bg-white border-radius-8 py-md px-lg" data-gap="md" data-wrap="no">
        <div class="flex-1">
          <div class="cluster">
            <km-input-flat class="km-heading-4 full-width text-black" :placeholder="m.common_name()" :model-value="name" :readonly="recordReadonly" @change="name = $event" />
          </div>
          <div class="cluster">
            <km-input-flat class="km-description full-width text-black" :placeholder="m.common_description()" :model-value="description" :readonly="recordReadonly" @change="description = $event" />
          </div>
          <div class="cluster pl-sm">
            <km-glyph class="flex-none" name="info" tone="subtle">
              <km-tooltip class="bg-white block-shadow text-black km-description" self="top middle" :offset="[-50, -50]">System name serves as unique record id</km-tooltip>
            </km-glyph>
            <km-input-flat class="flex-1 km-flex-min-w-0 km-description full-width" :placeholder="m.placeholder_enterSystemNameReadable()" :model-value="system_name" :readonly="recordReadonly" @change="system_name = $event" @focus="showInfo = true" @blur="showInfo = false" />
          </div>
          <div v-if="showInfo" class="km-description text-secondary pl-sm">It is highly recommended to fill in system name only once and not change it later.</div>
        </div>
        <div class="flex-none cluster ml-md" data-align="start" data-wrap="no" data-gap="sm">
          <km-btn :label="m.common_recordInfo()" flat icon="info" icon-size="16px">
            <template #tooltip>
              <div class="p-sm">
                <div class="mb-sm">
                  <div class="text-secondary-text km-button-xs-text">Created:</div>
                  <div class="text-secondary-text km-description">{{ created_at }}</div>
                </div>
                <div class="mb-sm">
                  <div class="text-secondary-text km-button-xs-text">Modified:</div>
                  <div class="text-secondary-text km-description">{{ updated_at }}</div>
                </div>
                <div class="mb-sm">
                  <div class="text-secondary-text km-button-xs-text">Created by:</div>
                  <div class="text-secondary-text km-description">{{ created_by }}</div>
                </div>
                <div>
                  <div class="text-secondary-text km-button-xs-text">Modified by:</div>
                  <div class="text-secondary-text km-description">{{ updated_by }}</div>
                </div>
              </div>
            </template>
          </km-btn>
          <km-btn :label="m.common_createRun()" flat icon="play" icon-size="16px" @click="showRunDialog = true" />
          <km-btn v-if="!recordReadonly" :label="m.common_save()" flat icon="save" icon-size="16px" :loading="saving" :disable="saving" @click="save" />
          <km-glyph v-if="recordReadonly" name="lock" size="16px" tone="muted" :title="m.access_readOnlyTooltip()" data-test="deep-research-readonly-icon" />
          <ds-dropdown-menu-root>
            <ds-dropdown-menu-trigger as-child>
              <km-btn class="px-xs" flat icon="more-vertical" size="13px" />
            </ds-dropdown-menu-trigger>
            <ds-dropdown-menu-content side="bottom" align="end" :side-offset="4">
              <ds-dropdown-menu-item :disabled="!canCreate" @select="canCreate && (showCloneDialog = true)">Clone</ds-dropdown-menu-item>
              <ds-dropdown-menu-item v-if="canDelete" variant="destructive" @select="showDeleteDialog = true">Delete</ds-dropdown-menu-item>
            </ds-dropdown-menu-content>
          </ds-dropdown-menu-root>
          <km-popup-confirm :visible="showDeleteDialog" confirm-button-label="Delete Deep Research Config" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="confirmDelete" @cancel="showDeleteDialog = false">
            <div class="cluster km-heading-7" data-justify="center">You are about to delete the Deep Research Config</div>
            <div class="cluster text-center" data-justify="center">This action will permanently delete the configuration and cannot be undone.</div>
          </km-popup-confirm>
        </div>
      </div>
      <deep-research-configs-create-new v-if="showCloneDialog" :show-new-dialog="showCloneDialog" copy @cancel="showCloneDialog = false" @created="onCloned" />
      <km-dialog v-model="showRunDialog">
        <km-card style="min-inline-size: 600px">
          <div class="km-card-section">
            <div class="text-h6">Create New Run</div>
          </div>
          <div class="km-card-section pt-0">
            <div class="km-field mb-md">
              <div class="text-secondary-text pb-xs">Config</div>
              <km-input :model-value="name" height="30px" readonly />
              <div class="km-description text-secondary-text pt-2xs">This run will use the current configuration</div>
            </div>
            <div class="km-field mb-md">
              <div class="text-secondary-text pb-xs">Input (JSON)</div>
              <km-input v-model="runInput" type="textarea" outlined rows="8" :placeholder="m.deepResearch_exampleQuery()" />
              <div class="km-description text-secondary-text pt-2xs">Provide the input data for the research run</div>
            </div>
            <div class="km-field mb-md">
              <div class="text-secondary-text pb-xs">Client ID (optional)</div>
              <km-input v-model="runClientId" height="30px" :placeholder="m.deepResearch_optionalClientIdentifier()" />
            </div>
          </div>
          <div class="km-card-actions" align="right">
            <km-btn flat :label="m.common_cancel()" @click="showRunDialog = false" />
            <km-btn :label="m.common_createRun()" :loading="creatingRun" @click="createRun" />
          </div>
        </km-card>
      </km-dialog>
      <div :inert="recordReadonly" :class="recordReadonly ? 'deep-research-readonly-zone' : null" class="flex-1 ba-border bg-white border-radius-12 p-lg overflow-auto" style="min-block-size: 0">
        <div class="km-heading-6 mb-md">General Settings</div>
        <div class="gap-md">
          <div class="km-field">
            <div class="text-secondary-text pb-xs">Max Iterations</div>
            <div style="max-inline-size: 200px">
              <km-input v-model="maxIterations" type="number" height="30px" />
            </div>
            <div class="km-description text-secondary-text pt-2xs">Maximum number of research iterations</div>
          </div>
          <div class="km-field">
            <div class="text-secondary-text pb-xs">Max Results</div>
            <div style="max-inline-size: 200px">
              <km-input v-model="maxResults" type="number" height="30px" />
            </div>
            <div class="km-description text-secondary-text pt-2xs">Maximum number of search results per iteration</div>
          </div>
          <div class="km-field">
            <div class="text-secondary-text pb-xs">Parallel Tool Calls</div>
            <km-toggle v-model="config.config.parallel_tool_calls" />
            <div class="km-description text-secondary-text pt-2xs">Enable parallel tool calls for reasoning step (OpenAI only)</div>
          </div>
        </div>
        <km-separator />
        <div class="full-width" />
        <div class="km-heading-6 mb-md">Prompts</div>
        <div class="gap-md">
          <div class="km-field">
            <div class="text-secondary-text pb-xs">Reasoning Prompt</div>
            <div class="cluster" data-gap="sm">
              <div class="flex-1">
                <km-select v-model="config.config.reasoning_prompt" :options="promptTemplates" option-label="name" option-value="system_name" emit-value map-options has-dropdown-search height="30px" />
              </div>
              <div v-if="config.config.reasoning_prompt" class="flex-none">
                <km-btn icon="external-link" flat dense @click="navigateToPrompt(config.config.reasoning_prompt)" />
              </div>
            </div>
            <div class="km-description text-secondary-text pt-2xs">Prompt for generating reasoning and search queries</div>
          </div>
          <div class="km-field">
            <div class="text-secondary-text pb-xs">Analyze Search Results Prompt</div>
            <div class="cluster" data-gap="sm">
              <div class="flex-1">
                <km-select v-model="config.config.analyze_search_results_prompt" :options="promptTemplates" option-label="name" option-value="system_name" emit-value map-options has-dropdown-search height="30px" />
              </div>
              <div v-if="config.config.analyze_search_results_prompt" class="flex-none">
                <km-btn icon="external-link" flat dense @click="navigateToPrompt(config.config.analyze_search_results_prompt)" />
              </div>
            </div>
            <div class="km-description text-secondary-text pt-2xs">Prompt for analyzing search results</div>
          </div>
          <div class="km-field">
            <div class="text-secondary-text pb-xs">Process Search Result Prompt</div>
            <div class="cluster" data-gap="sm">
              <div class="flex-1">
                <km-select v-model="config.config.process_search_result_prompt" :options="promptTemplates" option-label="name" option-value="system_name" emit-value map-options has-dropdown-search height="30px" />
              </div>
              <div v-if="config.config.process_search_result_prompt" class="flex-none">
                <km-btn icon="external-link" flat dense @click="navigateToPrompt(config.config.process_search_result_prompt)" />
              </div>
            </div>
            <div class="km-description text-secondary-text pt-2xs">Prompt for processing individual search results</div>
          </div>
        </div>
        <km-separator />
        <div class="full-width" />
        <div class="cluster mb-md" data-justify="between">
          <div class="km-heading-6">Webhook</div>
          <km-toggle v-model="webhookEnabled" :label="m.common_enableWebhook()" />
        </div>
        <div v-if="webhookEnabled" class="gap-md">
          <div class="km-field">
            <div class="text-secondary-text pb-xs">API Server</div>
            <div class="cluster" data-gap="sm">
              <div class="flex-1">
                <km-select v-model="webhookApiServer" :options="apiServers" option-label="name" option-value="system_name" emit-value map-options height="30px" clearable />
              </div>
              <div v-if="webhookApiServer" class="flex-none">
                <km-btn icon="external-link" flat dense @click="navigateToApiServer(webhookApiServer)" />
              </div>
            </div>
            <div class="km-description text-secondary-text pt-2xs">API server for webhook calls</div>
          </div>
          <div class="km-field">
            <div class="text-secondary-text pb-xs">API Tool</div>
            <div class="cluster" data-gap="sm">
              <div class="flex-1">
                <km-select v-model="webhookApiTool" :options="availableTools" option-label="label" option-value="value" emit-value map-options height="30px" clearable />
              </div>
              <div v-if="webhookApiTool" class="flex-none">
                <km-btn icon="external-link" flat dense @click="navigateToTool(webhookApiServer, webhookApiTool)" />
              </div>
            </div>
            <div class="km-description text-secondary-text pt-2xs">Specific tool endpoint to call</div>
          </div>
          <div class="km-field">
            <div class="text-secondary-text pb-xs">Payload Template (JSON)</div>
            <km-input v-model="webhookPayloadString" type="textarea" rows="10" outlined :rules="[validateJSON]" :placeholder="m.deepResearch_exampleOutputMapping()" @blur="updatePayloadTemplate" />
            <div class="km-description text-secondary-text pt-2xs">Optional JSON template with path references (e.g., "run_id", "input.query", "result.summary")</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onActivated, watch, provide } from 'vue'
import { m } from '@/paraglide/messages'
import { useRouter, useRoute } from 'vue-router'
import { usePermissions } from '@shared'
import { useEntityQueries } from '@/queries/entities'
import { useDeepResearchStore } from '@/stores/deepResearchStore'
import { useNotify } from '@/composables/useNotify'
import DeepResearchConfigsCreateNew from './CreateNew.vue'

const drStore = useDeepResearchStore()
const router = useRouter()
const route = useRoute()
const { notifySuccess, notifyError } = useNotify()
const queries = useEntityQueries()

const { data: promptTemplatesListData } = queries.promptTemplates.useList()
const { data: apiServersListData } = queries.api_servers.useList()

const configId = ref(route.params.id)
const config = ref<any>(null)
const showInfo = ref(false)
const webhookPayloadString = ref('')
const saving = ref(false)
const showCloneDialog = ref(false)
const showDeleteDialog = ref(false)
const showRunDialog = ref(false)
const runInput = ref('{"task": ""}')
const runClientId = ref('')
const creatingRun = ref(false)

const loading = computed(() => !config.value)

// PR 10 — record-level permission gating.
const { can, canOn } = usePermissions()
const canEdit = computed(() => canOn(config.value, 'edit', 'deep_research'))
const canDelete = computed(() => canOn(config.value, 'delete', 'deep_research'))
const canCreate = computed(() => can('write:deep_research'))
const recordReadonly = computed(() => {
  const c = config.value
  if (!c) return false
  return canEdit.value === false
})
provide('deepResearchReadonly', recordReadonly)

// Computed properties for form fields
const name = computed({
  get: () => config.value?.name || '',
  set: (value) => {
    if (config.value) config.value.name = value
  }
})

const description = computed({
  get: () => config.value?.description || '',
  set: (value) => {
    if (config.value) config.value.description = value
  }
})

const system_name = computed({
  get: () => config.value?.system_name || '',
  set: (value) => {
    if (config.value) config.value.system_name = value
  }
})

// Numeric fields that need string/number conversion for km-input
const maxIterations = computed({
  get: () => config.value?.config?.max_iterations?.toString() || '',
  set: (value) => {
    if (config.value?.config) {
      config.value.config.max_iterations = parseInt(value) || 0
    }
  }
})

const maxResults = computed({
  get: () => config.value?.config?.max_results?.toString() || '',
  set: (value) => {
    if (config.value?.config) {
      config.value.config.max_results = parseInt(value) || 0
    }
  }
})

// Webhook configuration
const webhookEnabled = computed({
  get: () => config.value?.config?.webhook?.enabled ?? false,
  set: (value: boolean) => {
    if (!config.value?.config) return

    if (value) {
      // Enable: create webhook object or update existing
      if (!config.value.config.webhook) {
        config.value.config.webhook = {
          enabled: true,
          api_server: '',
          api_tool: '',
          payload_template: null
        }
      } else {
        config.value.config.webhook.enabled = true
      }
    } else {
      // Disable: just toggle the flag, keep the configuration
      if (config.value.config.webhook) {
        config.value.config.webhook.enabled = false
      }
    }
  }
})

const webhookApiServer = computed({
  get: () => config.value?.config?.webhook?.api_server || '',
  set: (value: string) => {
    if (!config.value?.config) return
    if (!config.value.config.webhook) {
      config.value.config.webhook = {
        enabled: true,
        api_server: value,
        api_tool: '',
        payload_template: null
      }
    } else {
      config.value.config.webhook.api_server = value
    }
  }
})

const webhookApiTool = computed({
  get: () => config.value?.config?.webhook?.api_tool || '',
  set: (value: string) => {
    if (!config.value?.config?.webhook) return
    config.value.config.webhook.api_tool = value
  }
})

// Simple validation function similar to the working example
const validateJSON = (val: string) => {
  if (!val.trim()) return true // Empty is ok
  try {
    JSON.parse(val)
    return true
  } catch (e) {
    return 'Invalid JSON'
  }
}

// Sync webhook payload between config and local string
watch(() => config.value?.config?.webhook?.payload_template, (newVal) => {
  if (newVal === null || newVal === undefined) {
    webhookPayloadString.value = ''
  } else if (typeof newVal === 'string') {
    webhookPayloadString.value = newVal
  } else {
    webhookPayloadString.value = JSON.stringify(newVal, null, 2)
  }
}, { immediate: true })

// Update config when user finishes editing (on blur)
const updatePayloadTemplate = () => {
  if (!config.value?.config?.webhook) return

  const value = webhookPayloadString.value.trim()
  if (!value) {
    config.value.config.webhook.payload_template = null
    return
  }

  try {
    config.value.config.webhook.payload_template = JSON.parse(value)
  } catch {
    // Keep the string value, don't clear it
    // The validation rule will show the error
  }
}

// Get prompt templates
const promptTemplates = computed(() => promptTemplatesListData.value?.items || [])

// Get API servers
const apiServers = computed(() => apiServersListData.value?.items || [])

// Get available tools for selected server
const availableTools = computed(() => {
  const serverName = webhookApiServer.value
  if (!serverName) return []
  const server = apiServers.value.find(
    (s: any) => s.system_name === serverName
  )
  return server?.tools?.map((t: any) => ({
    label: t.name,
    value: t.system_name
  })) || []
})

onMounted(async () => {
  await drStore.fetchConfigs()
  loadConfig()
})

onActivated(() => {
  configId.value = route.params.id
})

const loadConfig = () => {
  const configs = drStore.configs
  if (!Array.isArray(configs)) {

    return
  }
  const found = configs.find((c: any) => c.id === configId.value)
  if (found) {
    config.value = JSON.parse(JSON.stringify(found)) // Deep clone
    drStore.selectedConfig = found
  }
}

// Watch for route changes to reload config when navigating to different config
watch(() => configId.value, () => {
  loadConfig()
})

watch(() => drStore.configs, () => {
  if (!config.value) {
    loadConfig()
  }
})

watch(() => config.value, (newVal) => {
  if (newVal) {
    drStore.selectedConfig = newVal
  }
}, { deep: true })

const formatDate = (date: string) => {
  if (!date) return ''
  const d = new Date(date)
  return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`
}

const created_at = computed(() => formatDate(config.value?.created_at))
const updated_at = computed(() => formatDate(config.value?.updated_at))
const created_by = computed(() => config.value?.created_by || 'Unknown')
const updated_by = computed(() => config.value?.updated_by || 'Unknown')

const save = async () => {
  saving.value = true
  try {
    if (!config.value) throw new Error('No configuration loaded')

    if (config.value?.created_at) {
      await drStore.updateConfig({
        configId: configId.value as string,
        updates: {
          name: config.value.name,
          description: config.value.description,
          system_name: config.value.system_name,
          config: config.value.config,
        },
      })
    } else {
      await drStore.createConfig(config.value)
    }

    notifySuccess('Configuration saved successfully')
  } catch (error: any) {
    notifyError(error?.message || 'Failed to save configuration')
  } finally {
    saving.value = false
  }
}

const confirmDelete = async () => {
  showDeleteDialog.value = false
  try {
    await drStore.deleteConfig(configId.value as string)
    notifySuccess('Deep Research Config has been deleted')
    router.push('/deep-research/configs')
  } catch (error: any) {
    notifyError(error?.message || 'Failed to delete configuration')
  }
}

const onCloned = (newConfigId: string) => {
  showCloneDialog.value = false
  router.push(`/deep-research/configs/${newConfigId}`)
}

const createRun = async () => {
  let inputPayload
  try {
    inputPayload = JSON.parse(runInput.value)
  } catch (e) {
    notifyError('Invalid JSON input')
    return
  }

  creatingRun.value = true
  try {
    const result = await drStore.createRun({
      config: config.value?.config || {},
      input: inputPayload,
      client_id: runClientId.value || undefined,
      config_system_name: config.value?.system_name,
    })

    notifySuccess('Run has been created')

    showRunDialog.value = false
    runInput.value = '{"task": ""}'
    runClientId.value = ''

    if (result?.id) {
      router.push(`/deep-research/runs/${result.id}`)
    }
  } catch (error: any) {
    notifyError(error?.message || 'Failed to create run')
  } finally {
    creatingRun.value = false
  }
}

const navigateToPrompt = (systemName: string) => {
  const prompt = promptTemplates.value.find((p: any) => p.system_name === systemName)
  if (prompt) {
    router.push(`/prompt-templates/${prompt.id}`)
  }
}

const navigateToApiServer = (systemName: string) => {
  const server = apiServers.value.find((s: any) => s.system_name === systemName)
  if (server) {
    router.push(`/api-servers/${server.id}`)
  }
}

const navigateToTool = (serverSystemName: string, toolName: string) => {
  const server = apiServers.value.find((s: any) => s.system_name === serverSystemName)
  if (server) {
    router.push(`/api-servers/${server.id}?tool=${toolName}`)
  }
}
</script>

<style scoped>
.deep-research-readonly-zone {
  opacity: 0.72;
  cursor: not-allowed;
}
.deep-research-readonly-zone :where(input, textarea, select, button, [role='button']) {
  cursor: not-allowed;
}
</style>


