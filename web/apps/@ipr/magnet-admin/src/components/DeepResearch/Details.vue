<template lang="pug">
.row.no-wrap.overflow-hidden.full-height(v-if='loading', style='min-width: 1200px')
  q-inner-loading(:showing='loading')
    q-spinner-gears(size='50px', color='primary')
.row.no-wrap.overflow-hidden.full-height(v-else, style='min-width: 1200px')
  .col.row.no-wrap.full-height.justify-center.fit
    .col(style='max-width: 1200px; min-width: 600px')
      .full-height.q-pb-md.relative-position.q-px-md
        //- Header section
        .row.items-center.q-gap-12.no-wrap.full-width.q-mt-lg.q-mb-sm.bg-white.border-radius-8.q-py-12.q-px-16
          .col
            .row.items-center
              km-input-flat.km-heading-4.full-width.text-black(placeholder='Name', v-model='name')
            .row.items-center
              km-input-flat.km-description.full-width.text-black(placeholder='Description', v-model='description')
            .row.items-center.q-pl-6
              q-icon.col-auto(name='o_info', color='text-secondary')
                q-tooltip.bg-white.block-shadow.text-black.km-description(self='top middle', :offset='[-50, -50]') System name serves as unique record id
              km-input-flat.col.km-description.full-width(
                placeholder='Enter system name',
                v-model='system_name',
                :readonly='true'
              )
            .km-description.text-secondary.q-pl-6 It is highly recommended to fill in system name only once and not change it later.

          //- Save and actions
          .col-auto
            .row.items-center.q-gutter-sm
              km-btn(
                label='Create Run',
                icon='play_arrow',
                @click='openCreateRunDialog'
              )
              km-btn(
                label='Save',
                icon='save',
                @click='saveAll',
                :loading='saving'
              )
              q-btn-dropdown(flat, round, dense, icon='more_vert')
                q-list
                  q-item(clickable, v-close-popup, @click='cloneConfig')
                    q-item-section(avatar)
                      q-icon(name='content_copy')
                    q-item-section
                      q-item-label Clone
                  q-item(clickable, v-close-popup, @click='confirmDelete')
                    q-item-section(avatar)
                      q-icon(name='delete', color='negative')
                    q-item-section
                      q-item-label.text-negative Delete

        //- Main content area
        .ba-border.bg-white.border-radius-12.q-pa-16(style='min-width: 300px')
          .column.no-wrap.q-gap-24.full-height.full-width.overflow-auto.q-mb-md(style='max-height: calc(100vh - 300px) !important')
            .col-auto.full-width
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
                  label='Enable Webhook'
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
                    v-model='webhookPayloadJson',
                    type='textarea',
                    rows='10',
                    outlined,
                    placeholder='Optional: {"run_id": "run_id", "result": "result.summary"}'
                  )
                  .km-description.text-secondary-text.q-pt-2 Optional JSON template with path references (e.g., "run_id", "input.query", "result.summary")

  //- Create Run Dialog
  q-dialog(v-model='showCreateRunDialog')
    q-card(style='min-width: 500px')
      q-card-section
        .text-h6 Create New Run
      q-card-section
        .text-subtitle2.q-mb-sm Input (JSON)
        q-input(
          v-model='runInput',
          type='textarea',
          rows='8',
          outlined,
          autofocus,
          placeholder='{"query": "Your research question here"}',
          :error='runInput.trim() && !isValidJson',
          error-message='Invalid JSON format'
        )
        .text-caption.text-grey-7.q-mt-xs Enter any valid JSON object. Example: {"query": "Research topic or question", "context": "Additional context"}
      q-card-actions(align='right')
        q-btn(flat, label='Cancel', color='primary', v-close-popup)
        q-btn(
          flat,
          label='Create',
          color='primary',
          @click='createRun',
          :disable='!runInput.trim() || !isValidJson'
        )
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useStore } from 'vuex'
import { useRouter, useRoute } from 'vue-router'
import { Notify, Dialog } from 'quasar'

const store = useStore()
const router = useRouter()
const route = useRoute()

const configId = computed(() => route.params.id as string)
const config = ref<any>(null)
const saving = ref(false)
const showCreateRunDialog = ref(false)
const runInput = ref('{"query": ""}')

const loading = computed(() => !config.value)

// Validate JSON input
const isValidJson = computed(() => {
  const trimmedInput = runInput.value.trim()
  if (!trimmedInput) return false
  try {
    const parsed = JSON.parse(trimmedInput)
    return typeof parsed === 'object' && parsed !== null
  } catch {
    return false
  }
})

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
  set: () => {} // Read-only
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

const webhookPayloadJson = computed({
  get: () => {
    const template = config.value?.config?.webhook?.payload_template
    if (!template) return ''
    if (typeof template === 'string') return template
    return JSON.stringify(template, null, 2)
  },
  set: (value: string) => {
    if (!config.value?.config?.webhook) return
    if (!value.trim()) {
      config.value.config.webhook.payload_template = null
      return
    }
    try {
      config.value.config.webhook.payload_template = JSON.parse(value)
    } catch {
      // Keep null if invalid JSON (user is still typing)
      config.value.config.webhook.payload_template = null
    }
  }
})

// Get prompt templates
const promptTemplates = computed(() => {
  const prompts = store.getters['chroma/promptTemplates']?.items || []
  return prompts
})

// Get API servers
const apiServers = computed(() => {
  const servers = store.getters['chroma/api_servers']?.items || []
  return servers
})

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
  await store.dispatch('fetchConfigs')

  // Fetch prompt templates and API servers if not already loaded
  if (!store.getters['chroma/promptTemplates']?.items?.length) {
    store.dispatch('chroma/promptTemplates/get')
  }
  if (!store.getters['chroma/api_servers']?.items?.length) {
    store.dispatch('chroma/api_servers/get')
  }

  loadConfig()
})

const loadConfig = () => {
  const configs = store.getters.configs
  if (!Array.isArray(configs)) {
    console.warn('Configs is not an array:', configs)
    return
  }
  const found = configs.find((c: any) => c.id === configId.value)
  if (found) {
    config.value = JSON.parse(JSON.stringify(found)) // Deep clone
  }
}

watch(() => store.getters.configs, () => {
  if (!config.value) {
    loadConfig()
  }
})

const saveAll = async () => {
  if (!config.value) return

  saving.value = true
  try {
    await store.dispatch('updateConfig', {
      configId: configId.value,
      updates: {
        name: config.value.name,
        description: config.value.description,
        config: config.value.config,
      },
    })

    Notify.create({
      type: 'positive',
      message: 'Configuration saved successfully',
      position: 'top',
      timeout: 1500,
    })
  } catch (error: any) {
    Notify.create({
      type: 'negative',
      message: error?.message || 'Failed to save configuration',
      position: 'top',
      timeout: 2000,
    })
  } finally {
    saving.value = false
  }
}

const cloneConfig = async () => {
  if (!config.value) return

  try {
    const result = await store.dispatch('createConfig', {
      name: `${config.value.name} (Copy)`,
      system_name: `${config.value.system_name}_COPY_${Date.now()}`,
      config: config.value.config,
    })

    Notify.create({
      type: 'positive',
      message: 'Configuration cloned successfully',
      position: 'top',
      timeout: 1500,
    })

    router.push(`/deep-research/configs/${result.id}`)
  } catch (error: any) {
    Notify.create({
      type: 'negative',
      message: error?.message || 'Failed to clone configuration',
      position: 'top',
      timeout: 2000,
    })
  }
}

const confirmDelete = () => {
  Dialog.create({
    title: 'Confirm Delete',
    message: 'Are you sure you want to delete this configuration? This action cannot be undone.',
    cancel: true,
    persistent: true,
  }).onOk(async () => {
    try {
      await store.dispatch('deleteConfig', configId.value)

      Notify.create({
        type: 'positive',
        message: 'Configuration deleted successfully',
        position: 'top',
        timeout: 1500,
      })

      router.push('/deep-research/configs')
    } catch (error: any) {
      Notify.create({
        type: 'negative',
        message: error?.message || 'Failed to delete configuration',
        position: 'top',
        timeout: 2000,
      })
    }
  })
}

const navigateToPrompt = (systemName: string) => {
  const prompt = promptTemplates.value.find((p: any) => p.system_name === systemName)
  if (prompt) {
    window.open(`/prompt-templates/${prompt.id}`, '_blank')
  }
}

const navigateToApiServer = (systemName: string) => {
  const server = apiServers.value.find((s: any) => s.system_name === systemName)
  if (server) {
    window.open(`/api-servers/${server.id}`, '_blank')
  }
}

const navigateToTool = (serverSystemName: string, toolName: string) => {
  const server = apiServers.value.find((s: any) => s.system_name === serverSystemName)
  if (server) {
    window.open(`/api-servers/${server.id}?tool=${toolName}`, '_blank')
  }
}

const openCreateRunDialog = () => {
  showCreateRunDialog.value = true
}

const createRun = async () => {
  if (!runInput.value.trim() || !config.value || !isValidJson.value) return

  try {
    const inputData = JSON.parse(runInput.value)

    const result = await store.dispatch('createRun', {
      config: config.value.config,
      input: inputData,
      client_id: null,
    })

    Notify.create({
      type: 'positive',
      message: 'Run started successfully',
      position: 'top',
      timeout: 1500,
    })

    showCreateRunDialog.value = false
    runInput.value = '{"query": ""}'

    // Optionally navigate to run details
    const runId = result?.id ?? result?.run_id
    if (runId) {
      router.push(`/deep-research/runs/${runId}`)
    }
  } catch (error: any) {
    Notify.create({
      type: 'negative',
      message: error?.message || 'Failed to start run',
      position: 'top',
      timeout: 2000,
    })
  }
}
</script>

<style lang="stylus" scoped>
.collection-container {
  min-width: 600px;
  max-width: 1200px;
  width: 100%;
}
</style>
