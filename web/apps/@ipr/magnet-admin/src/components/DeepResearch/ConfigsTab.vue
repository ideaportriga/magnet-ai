<template lang="pug">
.column.q-gap-16
  .row.items-center.justify-between
    .km-heading-5.text-black Research Configurations
    q-btn.km-btn(
      label='New Config',
      icon='add',
      color='primary',
      unelevated,
      @click='showCreateDialog = true'
    )

  q-card.q-pa-md(v-if='loading')
    q-inner-loading(:showing='loading')
      q-spinner(color='primary', size='50px')

  .column.q-gap-12(v-else-if='configs.length > 0')
    q-card.q-pa-md(v-for='config in configs', :key='config.id')
      .row.items-center.justify-between
        .column
          .km-title.text-black {{ config.name }}
          .km-description.text-secondary.q-mt-xs Max iterations: {{ config.config.max_iterations }} | Max results: {{ config.config.max_results }}
        .row.q-gap-8
          q-btn(
            flat,
            dense,
            icon='play_arrow',
            color='primary',
            @click='triggerRun(config)'
          )
            q-tooltip Run with this config
          q-btn(
            flat,
            dense,
            icon='delete',
            color='negative',
            @click='deleteConfig(config.id)'
          )
            q-tooltip Delete config

      q-separator.q-my-md

      .row.q-col-gutter-md
        .col-6
          .km-description.text-secondary Reasoning Prompt
          .row.items-center.q-gap-xs
            .km-label.text-black {{ config.config.reasoning_prompt }}
            q-btn(
              flat,
              dense,
              icon='open_in_new',
              size='xs',
              @click='navigateToPromptOrList(config.config.reasoning_prompt, "prompt-templates")'
            )
        .col-6
          .km-description.text-secondary Analyze Search Results Prompt
          .row.items-center.q-gap-xs
            .km-label.text-black {{ config.config.analyze_search_results_prompt }}
            q-btn(
              flat,
              dense,
              icon='open_in_new',
              size='xs',
              @click='navigateToPromptOrList(config.config.analyze_search_results_prompt, "prompt-templates")'
            )
        .col-6
          .km-description.text-secondary Process Search Result Prompt
          .row.items-center.q-gap-xs
            .km-label.text-black {{ config.config.process_search_result_prompt }}
            q-btn(
              flat,
              dense,
              icon='open_in_new',
              size='xs',
              @click='navigateToPromptOrList(config.config.process_search_result_prompt, "prompt-templates")'
            )
        .col-6(v-if='config.config.webhook_tool_server')
          .km-description.text-secondary Webhook
          .row.items-center.q-gap-xs
            .km-label.text-black {{ config.config.webhook_tool_server }}/{{ config.config.webhook_tool_name }}
            q-btn(
              flat,
              dense,
              icon='open_in_new',
              size='xs',
              @click='navigateToApiServers()'
            )

  q-card.q-pa-md(v-else)
    .text-center.text-secondary No configs created yet

// Create Config Dialog
q-dialog(v-model='showCreateDialog')
  q-card(style='min-width: 600px')
    q-card-section
      .text-h6 Create Research Config

    q-card-section.q-pt-none
      q-form(@submit='createConfig')
        q-input.q-mb-md(
          v-model='newConfig.name',
          label='Config Name',
          outlined,
          dense,
          :rules='[val => !!val || "Name is required"]'
        )

        q-input.q-mb-md(
          v-model.number='newConfig.config.max_iterations',
          label='Max Iterations',
          type='number',
          outlined,
          dense,
          :rules='[val => val >= 1 && val <= 30 || "Must be between 1 and 30"]'
        )

        q-input.q-mb-md(
          v-model.number='newConfig.config.max_results',
          label='Max Results per Query',
          type='number',
          outlined,
          dense,
          :rules='[val => val >= 1 && val <= 20 || "Must be between 1 and 20"]'
        )

        q-input.q-mb-md(
          v-model='newConfig.config.reasoning_prompt',
          label='Reasoning Prompt Template',
          outlined,
          dense,
          hint='System name of the prompt template'
        )
          template(#append)
            q-btn(
              flat,
              dense,
              icon='open_in_new',
              size='sm',
              @click='navigateToPromptOrList(newConfig.config.reasoning_prompt, "prompt-templates")'
            )
              q-tooltip Open Prompt Templates

        q-input.q-mb-md(
          v-model='newConfig.config.analyze_search_results_prompt',
          label='Analyze Search Results Prompt Template',
          outlined,
          dense,
          hint='System name of the prompt template'
        )
          template(#append)
            q-btn(
              flat,
              dense,
              icon='open_in_new',
              size='sm',
              @click='navigateToPromptOrList(newConfig.config.analyze_search_results_prompt, "prompt-templates")'
            )
              q-tooltip Open Prompt Templates

        q-input.q-mb-md(
          v-model='newConfig.config.process_search_result_prompt',
          label='Process Search Result Prompt Template',
          outlined,
          dense,
          hint='System name of the prompt template'
        )
          template(#append)
            q-btn(
              flat,
              dense,
              icon='open_in_new',
              size='sm',
              @click='navigateToPromptOrList(newConfig.config.process_search_result_prompt, "prompt-templates")'
            )
              q-tooltip Open Prompt Templates

        q-separator.q-my-md

        .text-subtitle2.q-mb-md Webhook (Optional)

        q-input.q-mb-md(
          v-model='newConfig.config.webhook_tool_server',
          label='Webhook API Server',
          outlined,
          dense,
          hint='System name of the API server'
        )
          template(#append)
            q-btn(
              flat,
              dense,
              icon='open_in_new',
              size='sm',
              @click='navigateToApiServers()'
            )
              q-tooltip Open API Servers

        q-input.q-mb-md(
          v-model='newConfig.config.webhook_tool_name',
          label='Webhook Tool Name',
          outlined,
          dense,
          hint='System name of the API tool'
        )

        q-card-actions(align='right')
          q-btn(flat, label='Cancel', color='grey', v-close-popup)
          q-btn(type='submit', label='Create', color='primary', unelevated)

// Trigger Run Dialog
q-dialog(v-model='showTriggerRunDialog')
  q-card(style='min-width: 500px')
    q-card-section
      .text-h6 Trigger Run: {{ selectedConfigForRun?.name }}

    q-card-section.q-pt-none
      q-form(@submit='submitTriggerRun')
        .text-subtitle2.q-mb-md Input Data (JSON)
        q-input.q-mb-md(
          v-model='runInput',
          type='textarea',
          outlined,
          dense,
          rows='8',
          :rules='[validateJSON]'
          placeholder='{"query": "Research question here", "context": "Additional context..."}'
        )

        q-input.q-mb-md(
          v-model='runClientId',
          label='Client ID (optional)',
          outlined,
          dense,
        )

        q-card-actions(align='right')
          q-btn(flat, label='Cancel', color='grey', v-close-popup)
          q-btn(type='submit', label='Run', color='primary', unelevated, :loading='triggering')
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useStore } from 'vuex'
import { Notify } from 'quasar'

const store = useStore()

const showCreateDialog = ref(false)
const showTriggerRunDialog = ref(false)
const triggering = ref(false)
const selectedConfigForRun = ref<any>(null)
const runInput = ref('{"query": ""}')
const runClientId = ref('')

const newConfig = ref({
  name: '',
  config: {
    reasoning_prompt: 'DEFAULT_DEEP_RESEARCH_REASONING',
    analyze_search_results_prompt: 'DEFAULT_DEEP_RESEARCH_ANALYZE_SEARCH_RESULTS',
    process_search_result_prompt: 'DEFAULT_DEEP_RESEARCH_PROCESS_SEARCH_RESULT',
    max_iterations: 10,
    max_results: 5,
    parallel_tool_calls: false,
    webhook_tool_server: null,
    webhook_tool_name: null,
    webhook_payload_template: null,
  },
})

const configs = computed(() => store.getters.configs || [])
const loading = computed(() => store.getters.loading)

const validateJSON = (val: string) => {
  try {
    JSON.parse(val)
    return true
  } catch (e) {
    return 'Invalid JSON'
  }
}

const createConfig = async () => {
  try {
    await store.dispatch('createConfig', {
      name: newConfig.value.name,
      config: newConfig.value.config,
    })

    Notify.create({
      type: 'positive',
      message: 'Config created successfully',
    })

    showCreateDialog.value = false

    // Reset form
    newConfig.value = {
      name: '',
      config: {
        reasoning_prompt: 'DEFAULT_DEEP_RESEARCH_REASONING',
        analyze_search_results_prompt: 'DEFAULT_DEEP_RESEARCH_ANALYZE_SEARCH_RESULTS',
        process_search_result_prompt: 'DEFAULT_DEEP_RESEARCH_PROCESS_SEARCH_RESULT',
        max_iterations: 10,
        max_results: 5,
        parallel_tool_calls: false,
        webhook_tool_server: null,
        webhook_tool_name: null,
        webhook_payload_template: null,
      },
    }
  } catch (error: any) {
    Notify.create({
      type: 'negative',
      message: error?.message || 'Failed to create config',
    })
  }
}

const deleteConfig = async (configId: string) => {
  if (!confirm('Are you sure you want to delete this config?')) {
    return
  }

  try {
    await store.dispatch('deleteConfig', configId)

    Notify.create({
      type: 'positive',
      message: 'Config deleted successfully',
    })
  } catch (error: any) {
    Notify.create({
      type: 'negative',
      message: error?.message || 'Failed to delete config',
    })
  }
}

const triggerRun = (config: any) => {
  selectedConfigForRun.value = config
  runInput.value = '{"query": ""}'
  runClientId.value = ''
  showTriggerRunDialog.value = true
}

const submitTriggerRun = async () => {
  if (!selectedConfigForRun.value) return

  try {
    triggering.value = true

    const inputData = JSON.parse(runInput.value)

    await store.dispatch('createRunFromConfig', {
      configId: selectedConfigForRun.value.id,
      input: inputData,
      client_id: runClientId.value || undefined,
    })

    Notify.create({
      type: 'positive',
      message: 'Run triggered successfully',
    })

    showTriggerRunDialog.value = false
  } catch (error: any) {
    Notify.create({
      type: 'negative',
      message: error?.message || 'Failed to trigger run',
    })
  } finally {
    triggering.value = false
  }
}

const navigateToPromptOrList = (promptSystemName: string | null, defaultPath: string) => {
  if (!promptSystemName || promptSystemName.startsWith('DEFAULT_')) {
    router.push(`/${defaultPath}`)
    return
  }

  // Try to find the prompt template ID by system name
  const promptTemplates = store.getters.chroma?.promptTemplates?.items || []
  const found = promptTemplates.find((p: any) => p.system_name === promptSystemName)

  if (found) {
    router.push(`/${defaultPath}/${found.id}`)
  } else {
    router.push(`/${defaultPath}`)
  }
}

const navigateToApiServers = () => {
  router.push('/api-servers')
}
</script>

<style scoped lang="scss">
.km-btn {
  text-transform: none;
}
</style>
