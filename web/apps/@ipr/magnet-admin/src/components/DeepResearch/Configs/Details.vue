<template lang="pug">
.row.no-wrap.overflow-hidden.full-height(v-if='loading', style='min-width: 1200px')
  km-inner-loading(:showing='loading')
.column.no-wrap.overflow-hidden.full-height(v-else)
  .q-mx-auto.full-width.column.full-height.q-px-md(style='max-width: 1200px; min-width: 600px')
    .row.items-center.q-gap-12.no-wrap.full-width.q-mt-lg.q-mb-sm.bg-white.border-radius-8.q-py-12.q-px-16
      .col
        .row.items-center
          km-input-flat.km-heading-4.full-width.text-black(:placeholder='m.common_name()', :model-value='name', @change='name = $event')
        .row.items-center
          km-input-flat.km-description.full-width.text-black(:placeholder='m.common_description()', :model-value='description', @change='description = $event')
        .row.items-center.q-pl-6
          q-icon.col-auto(name='o_info', color='text-secondary')
            q-tooltip.bg-white.block-shadow.text-black.km-description(self='top middle', :offset='[-50, -50]') System name serves as unique record id
          km-input-flat.col.km-description.full-width(
            :placeholder='m.placeholder_enterSystemNameReadable()',
            :model-value='system_name',
            @change='system_name = $event',
            @focus='showInfo = true',
            @blur='showInfo = false'
          )
        .km-description.text-secondary.q-pl-6(v-if='showInfo') It is highly recommended to fill in system name only once and not change it later.
      .col-auto.row.items-start.no-wrap.q-gap-8.q-ml-md
        km-btn(:label='m.common_recordInfo()', flat, icon='info', iconSize='16px')
          q-tooltip.bg-white.block-shadow
            .q-pa-sm
              .q-mb-sm
                .text-secondary-text.km-button-xs-text Created:
                .text-secondary-text.km-description {{ created_at }}
              .q-mb-sm
                .text-secondary-text.km-button-xs-text Modified:
                .text-secondary-text.km-description {{ updated_at }}
              .q-mb-sm
                .text-secondary-text.km-button-xs-text Created by:
                .text-secondary-text.km-description {{ created_by }}
              div
                .text-secondary-text.km-button-xs-text Modified by:
                .text-secondary-text.km-description {{ updated_by }}
        km-btn(:label='m.common_createRun()', flat, icon='play_arrow', iconSize='16px', @click='showRunDialog = true')
        km-btn(:label='m.common_save()', flat, icon='far fa-save', iconSize='16px', @click='save', :loading='saving', :disable='saving')
        q-btn.q-px-xs(flat, :icon='"fas fa-ellipsis-v"', size='13px')
          q-menu(anchor='bottom right', self='top right')
            q-item(clickable, @click='showCloneDialog = true', dense)
              q-item-section
                .km-heading-3 Clone
            q-item(clickable, @click='showDeleteDialog = true', dense)
              q-item-section
                .km-heading-3 Delete
        km-popup-confirm(
          :visible='showDeleteDialog',
          confirmButtonLabel='Delete Deep Research Config',
          :cancelButtonLabel='m.common_cancel()',
          notificationIcon='fas fa-triangle-exclamation',
          @confirm='confirmDelete',
          @cancel='showDeleteDialog = false'
        )
          .row.item-center.justify-center.km-heading-7 You are about to delete the Deep Research Config
          .row.text-center.justify-center This action will permanently delete the configuration and cannot be undone.
    deep-research-configs-create-new(v-if='showCloneDialog', :showNewDialog='showCloneDialog', @cancel='showCloneDialog = false', @created='onCloned', copy)
    q-dialog(v-model='showRunDialog')
      q-card(style='min-width: 600px')
        q-card-section
          .text-h6 Create New Run
        q-card-section.q-pt-none
          .km-field.q-mb-md
            .text-secondary-text.q-pb-xs Config
            km-input(
              :model-value='name',
              height='30px',
              readonly
            )
            .km-description.text-secondary-text.q-pt-2 This run will use the current configuration
          .km-field.q-mb-md
            .text-secondary-text.q-pb-xs Input (JSON)
            q-input(
              v-model='runInput',
              type='textarea',
              outlined,
              rows='8',
              :placeholder='m.deepResearch_exampleQuery()'
            )
            .km-description.text-secondary-text.q-pt-2 Provide the input data for the research run
          .km-field.q-mb-md
            .text-secondary-text.q-pb-xs Client ID (optional)
            km-input(
              v-model='runClientId',
              height='30px',
              :placeholder='m.deepResearch_optionalClientIdentifier()'
            )
        q-card-actions(align='right')
          km-btn(flat, :label='m.common_cancel()', @click='showRunDialog = false')
          km-btn(:label='m.common_createRun()', :loading='creatingRun', @click='createRun')
    .col.ba-border.bg-white.border-radius-12.q-pa-16.overflow-auto(style='min-height: 0')
      .km-heading-6.q-mb-md General Settings
      .q-gutter-md
        .km-field
          .text-secondary-text.q-pb-xs Max Iterations
          div(style='max-width: 200px')
            km-input(
              v-model='maxIterations',
              type='number',
              height='30px'
            )
          .km-description.text-secondary-text.q-pt-2 Maximum number of research iterations

        .km-field
          .text-secondary-text.q-pb-xs Max Results
          div(style='max-width: 200px')
            km-input(
              v-model='maxResults',
              type='number',
              height='30px'
            )
          .km-description.text-secondary-text.q-pt-2 Maximum number of search results per iteration

        .km-field
          .text-secondary-text.q-pb-xs Parallel Tool Calls
          q-toggle(
            v-model='config.config.parallel_tool_calls',
            color='primary'
          )
          .km-description.text-secondary-text.q-pt-2 Enable parallel tool calls for reasoning step (OpenAI only)

      q-separator

      //- Prompts Section
      .col-auto.full-width
      .km-heading-6.q-mb-md Prompts
      .q-gutter-md
        .km-field
          .text-secondary-text.q-pb-xs Reasoning Prompt
          .row.items-center.q-gutter-sm
            .col
              km-select(
                v-model='config.config.reasoning_prompt',
                :options='promptTemplates',
                option-label='name',
                option-value='system_name',
                emit-value,
                map-options,
                hasDropdownSearch,
                height='30px'
              )
            .col-auto(v-if='config.config.reasoning_prompt')
              km-btn(
                icon='open_in_new',
                flat,
                dense,
                @click='navigateToPrompt(config.config.reasoning_prompt)'
              )
          .km-description.text-secondary-text.q-pt-2 Prompt for generating reasoning and search queries

        .km-field
          .text-secondary-text.q-pb-xs Analyze Search Results Prompt
          .row.items-center.q-gutter-sm
            .col
              km-select(
                v-model='config.config.analyze_search_results_prompt',
                :options='promptTemplates',
                option-label='name',
                option-value='system_name',
                emit-value,
                map-options,
                hasDropdownSearch,
                height='30px'
              )
            .col-auto(v-if='config.config.analyze_search_results_prompt')
              km-btn(
                icon='open_in_new',
                flat,
                dense,
                @click='navigateToPrompt(config.config.analyze_search_results_prompt)'
              )
          .km-description.text-secondary-text.q-pt-2 Prompt for analyzing search results

        .km-field
          .text-secondary-text.q-pb-xs Process Search Result Prompt
          .row.items-center.q-gutter-sm
            .col
              km-select(
                v-model='config.config.process_search_result_prompt',
                :options='promptTemplates',
                option-label='name',
                option-value='system_name',
                emit-value,
                map-options,
                hasDropdownSearch,
                height='30px'
              )
            .col-auto(v-if='config.config.process_search_result_prompt')
              km-btn(
                icon='open_in_new',
                flat,
                dense,
                @click='navigateToPrompt(config.config.process_search_result_prompt)'
              )
          .km-description.text-secondary-text.q-pt-2 Prompt for processing individual search results

      q-separator

      //- Webhook Section
      .col-auto.full-width
      .row.items-center.justify-between.q-mb-md
        .km-heading-6 Webhook
        q-toggle(
          v-model='webhookEnabled',
          color='primary',
          :label='m.common_enableWebhook()'
        )
              
      .q-gutter-md(v-if='webhookEnabled')
        .km-field
          .text-secondary-text.q-pb-xs API Server
          .row.items-center.q-gutter-sm
            .col
              km-select(
                v-model='webhookApiServer',
                :options='apiServers',
                option-label='name',
                option-value='system_name',
                emit-value,
                map-options,
                height='30px',
                clearable
              )
            .col-auto(v-if='webhookApiServer')
              km-btn(
                icon='open_in_new',
                flat,
                dense,
                @click='navigateToApiServer(webhookApiServer)'
              )
          .km-description.text-secondary-text.q-pt-2 API server for webhook calls

        .km-field
          .text-secondary-text.q-pb-xs API Tool
          .row.items-center.q-gutter-sm
            .col
              km-select(
                v-model='webhookApiTool',
                :options='availableTools',
                option-label='label',
                option-value='value',
                emit-value,
                map-options,
                height='30px',
                clearable
              )
            .col-auto(v-if='webhookApiTool')
              km-btn(
                icon='open_in_new',
                flat,
                dense,
                @click='navigateToTool(webhookApiServer, webhookApiTool)'
              )
          .km-description.text-secondary-text.q-pt-2 Specific tool endpoint to call

        .km-field
          .text-secondary-text.q-pb-xs Payload Template (JSON)
          q-input(
            v-model='webhookPayloadString',
            type='textarea',
            rows='10',
            outlined,
            :rules='[validateJSON]',
            @blur='updatePayloadTemplate',
            :placeholder='m.deepResearch_exampleOutputMapping()'
          )
          .km-description.text-secondary-text.q-pt-2 Optional JSON template with path references (e.g., "run_id", "input.query", "result.summary")
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onActivated, watch } from 'vue'
import { m } from '@/paraglide/messages'
import { useRouter, useRoute } from 'vue-router'
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


