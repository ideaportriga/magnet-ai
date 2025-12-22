<template lang="pug">
.row.no-wrap.overflow-hidden.full-height(v-if='loading', style='min-width: 1200px')
  q-inner-loading(:showing='loading')
    q-spinner-gears(size='50px', color='primary')
.row.no-wrap.overflow-hidden.full-height(v-else, style='min-width: 1200px')
  .col.row.no-wrap.full-height.justify-center.fit
    .col(style='max-width: 1200px; min-width: 600px')
      .full-height.q-pb-md.relative-position.q-px-md
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
                @focus='showInfo = true',
                @blur='showInfo = false'
              )
            .km-description.text-secondary.q-pl-6(v-if='showInfo') It is highly recommended to fill in system name only once and not change it later.
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
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useStore } from 'vuex'
import { useRouter, useRoute } from 'vue-router'
import { useQuasar } from 'quasar'

const store = useStore()
const router = useRouter()
const route = useRoute()
const $q = useQuasar()

const configId = computed(() => route.params.id as string)
const config = ref<any>(null)
const showInfo = ref(false)

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
    store.commit('setSelectedConfig', found)
  }
}

// Watch for route changes to reload config when navigating to different config
watch(() => configId.value, () => {
  loadConfig()
})

watch(() => store.getters.configs, () => {
  if (!config.value) {
    loadConfig()
  }
})

watch(() => config.value, (newVal) => {
  if (newVal) {
    store.commit('setSelectedConfig', newVal)
  }
}, { deep: true })

const navigateToPrompt = (systemName: string) => {
  const prompt = promptTemplates.value.find((p: any) => p.system_name === systemName)
  if (prompt) {
    window.open(router.resolve({ path: `/prompt-templates/${prompt.id}` }).href, '_blank')
  }
}

const navigateToApiServer = (systemName: string) => {
  const server = apiServers.value.find((s: any) => s.system_name === systemName)
  if (server) {
    window.open(router.resolve({ path: `/api-servers/${server.id}` }).href, '_blank')
  }
}

const navigateToTool = (serverSystemName: string, toolName: string) => {
  const server = apiServers.value.find((s: any) => s.system_name === serverSystemName)
  if (server) {
    window.open(router.resolve({ path: `/api-servers/${server.id}?tool=${toolName}` }).href, '_blank')
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
