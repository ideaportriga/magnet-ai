<template lang="pug">
km-drawer-layout(storageKey="drawer-model-providers-model", noScroll)
  template(#tabs)
    .q-pt-16.q-px-16
      q-tabs.bb-border.full-width(
        v-model='tab',
        narrow-indicator,
        dense,
        align='left',
        active-color='primary',
        indicator-color='primary',
        active-bg-color='white',
        no-caps,
        content-class='km-tabs'
      )
        template(v-for='t in tabs')
          q-tab(:name='t.name', :label='t.label')
        .fit
  //- DrawerLayout's default slot is already wrapped in
  //- `.col.km-drawer-content.overflow-auto` (noScroll branch), so the
  //- content here must be a plain block. A nested `.col.overflow-auto`
  //- creates double-flex-grow inside a flex column — the inner `.col`
  //- grows to fit content, overriding the outer scroll container, and
  //- the footer with "Test Model" gets pushed below the viewport.
  div
    .column.q-gap-16.q-pa-16(v-if='tab == "parameters"')
      .km-title General settings
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Name
        km-input(:model-value='model', @update:model-value='model = $event')
        .km-description.text-secondary-text.q-pl-8.q-pt-xs Name used by provider to identify the model
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Display name
        km-input(:model-value='display_name', @update:model-value='display_name = $event')
        .km-description.text-secondary-text.q-pl-8.q-pt-xs Internal name used across Magnet AI
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 System name
        km-input(:model-value='system_name', readonly)
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Type
        km-select(height='32px', :options='categoryOptions', :model-value='type', @update:model-value='type = $event', emit-value, map-options)
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Description
        km-input(:model-value='description', @update:model-value='description = $event')
      .q-mt-8
        .row.items-center.q-gap-8
          km-checkbox(:label='m.modelProviders_defaultModel()', :model-value='is_default', dense, disable)
          q-icon(name='o_info', size='16px', color='secondary-text')
            q-tooltip.bg-white.block-shadow.text-secondary-text.km-description(self='top middle', :offset='[-50, -50]') If marked as Default, model will be selected by default on related tools
          .q-ml
            km-btn(flat, :label='m.modelProviders_editDefaults()', color='primary', @click='goToDefaultModels')

      .q-mt-8
        km-checkbox(:label='m.common_activate()', :model-value='is_active', @update:model-value='is_active = $event')
        .km-description.text-secondary-text.q-pl-8.q-pt-xs When disabled, this model will not be available for selection

      q-separator.q-my-16

      // Features section for prompts models
      template(v-if='type === "prompts"')
        .km-title Features
        km-checkbox(:label='m.common_jsonMode()', :model-value='json_mode', @update:model-value='json_mode = $event')
        km-checkbox(:label='m.common_structuredOutputs()', :model-value='json_schema', @update:model-value='json_schema = $event')
        km-checkbox(:label='m.common_toolCalling()', :model-value='tool_calling', @update:model-value='tool_calling = $event')
        km-checkbox(:label='m.common_reasoning()', :model-value='reasoning', @update:model-value='reasoning = $event')

      // Vector configuration for embeddings models
      template(v-if='type === "embeddings"')
        .km-title Vector Configuration
        div
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Vector Size
          km-input(height='32px', type='number', :placeholder='m.placeholder_exampleVectorSize()', :model-value='vectorSize', @update:model-value='vectorSize = $event')
          .km-description.text-secondary-text.q-pl-8.q-pt-xs Dimension of the embedding vector. Common values: 1536 (ada-002), 1024 (embed-3-small), 3072 (embed-3-large)

    .column.q-gap-16.q-pa-16(v-if='tab == "pricing"')
      .km-title Inputs
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Input units
        km-select(
          height='32px',
          :options='priceUnitOptions',
          :model-value='price_input_unit_name',
          @update:model-value='price_input_unit_name = $event',
          emit-value,
          map-options
        )
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Price for standard input
        .row.items-center.q-gap-8.no-wrap
          km-input(
            prefix='$',
            height='32px',
            :model-value='price_standard_input',
            @update:model-value='price_standard_input = $event',
            style='max-width: 120px'
          )
          .text-secondary-text per
          km-input(
            height='32px',
            :model-value='price_standard_input_unit_count',
            @update:model-value='price_standard_input_unit_count = $event',
            style='max-width: 120px'
          )
          .text-secondary-text {{ price_input_unit_name }}
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Price for cached input
        .row.items-center.q-gap-8.no-wrap
          km-input(
            prefix='$',
            height='32px',
            :model-value='price_cached_input',
            @update:model-value='price_cached_input = $event',
            style='max-width: 120px'
          )
          .text-secondary-text per
          km-input(
            height='32px',
            :model-value='price_cached_input_unit_count',
            @update:model-value='price_cached_input_unit_count = $event',
            style='max-width: 120px'
          )
          .text-secondary-text {{ price_input_unit_name }}
      q-separator.q-my-16
      .km-title Outputs
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Output units
        km-select(
          height='32px',
          :options='priceUnitOptions',
          :model-value='price_output_unit_name',
          @update:model-value='price_output_unit_name = $event',
          emit-value,
          map-options
        )
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Price for standard output
        .row.items-center.q-gap-8.no-wrap
          km-input(
            prefix='$',
            height='32px',
            :model-value='price_standard_output',
            @update:model-value='price_standard_output = $event',
            style='max-width: 120px'
          )
          .text-secondary-text per
          km-input(
            height='32px',
            :model-value='price_standard_output_unit_count',
            @update:model-value='price_standard_output_unit_count = $event',
            style='max-width: 120px'
          )
          .text-secondary-text {{ price_output_unit_name }}
      template(v-if='reasoning')
        q-separator.q-my-16
        .km-title Reasoning Output
        div
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Price for reasoning output
          .row.items-center.q-gap-8.no-wrap
            km-input(
              prefix='$',
              height='32px',
              :model-value='price_reasoning_output',
              @update:model-value='price_reasoning_output = $event',
              style='max-width: 120px'
            )
            .text-secondary-text per
            km-input(
              height='32px',
              :model-value='price_reasoning_output_unit_count',
              @update:model-value='price_reasoning_output_unit_count = $event',
              style='max-width: 120px'
            )
            .text-secondary-text {{ price_output_unit_name }}


    //- Routing Config Tab
    .column.q-gap-16.q-pa-16(v-if='tab == "routing"')
      .km-title Endpoint
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 API Path
        km-input(:model-value='apiPath', @update:model-value='apiPath = $event', :placeholder='m.placeholder_exampleApiPath()')
        .km-description.text-secondary-text.q-pl-8.q-pt-xs
          | Path appended to the provider endpoint for this model. Must start with /.
          template(v-if="type === 're-ranking'")
            br
            | Azure AI Foundry rerank paths: /v1 → /v1/rerank, /v2 → /v2/rerank, /providers/cohere/v2 → /providers/cohere/v2/rerank
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Request URL
        .q-pa-xs.bg-grey-2.rounded-borders
          .text-caption.text-mono(style='word-break: break-all; white-space: normal') {{ debugInfo?.computed_url || '—' }}

      q-separator.q-my-16

      .km-title Caching
      km-checkbox(:label='m.common_enableResponseCaching()', :model-value='cacheEnabled', @update:model-value='cacheEnabled = $event')
      div(v-if='cacheEnabled')
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Cache TTL (seconds)
        km-input(height='32px', type='number', placeholder='3600', :model-value='cacheTtl', @update:model-value='cacheTtl = $event')
        .km-description.text-secondary-text.q-pl-8.q-pt-xs How long to cache responses (default: 3600 seconds = 1 hour)

      q-separator.q-my-16

      .km-title Rate Limiting
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Requests per Minute (RPM)
        km-input(height='32px', type='number', placeholder='60', :model-value='rpm', @update:model-value='rpm = $event')
        .km-description.text-secondary-text.q-pl-8.q-pt-xs Maximum requests per minute for this model
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Tokens per Minute (TPM)
        km-input(height='32px', type='number', placeholder='100000', :model-value='tpm', @update:model-value='tpm = $event')
        .km-description.text-secondary-text.q-pl-8.q-pt-xs Maximum tokens per minute for this model

      q-separator.q-my-16

      .km-title Reliability
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Number of Retries
        km-input(height='32px', type='number', placeholder='0', :model-value='numRetries', @update:model-value='numRetries = $event')
        .km-description.text-secondary-text.q-pl-8.q-pt-xs How many times to retry failed requests before fallback
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Retry After (seconds)
        km-input(height='32px', type='number', placeholder='0', :model-value='retryAfter', @update:model-value='retryAfter = $event')
        .km-description.text-secondary-text.q-pl-8.q-pt-xs Delay in seconds before retrying a failed request
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Timeout (seconds)
        km-input(height='32px', type='number', placeholder='60', :model-value='timeout', @update:model-value='timeout = $event')
        .km-description.text-secondary-text.q-pl-8.q-pt-xs Request timeout in seconds
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Fallback Models
        km-select(
          height='auto',
          minHeight='32px',
          multiple,
          use-chips,
          :placeholder='m.modelProviders_selectFallbackModels()',
          :options='availableFallbackModels',
          :model-value='fallbackModels',
          @update:model-value='fallbackModels = $event',
          emit-value,
          map-options
        )
        .km-description.text-secondary-text.q-pl-8.q-pt-xs Models to use as fallbacks when this model fails (can be from any provider)

      q-separator.q-my-16

      .km-title Load Balancing
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Priority
        km-input(height='32px', type='number', placeholder='1', :model-value='priority', @update:model-value='priority = $event')
        .km-description.text-secondary-text.q-pl-8.q-pt-xs Lower priority values are preferred (default: 1)
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Weight
        km-input(height='32px', type='number', placeholder='1', :model-value='weight', @update:model-value='weight = $event')
        .km-description.text-secondary-text.q-pl-8.q-pt-xs Weight for load balancing distribution (default: 1)

    //- Info Tab - Model capabilities from LiteLLM
    .column.q-gap-16.q-pa-16(v-if='tab == "info"')
      template(v-if='capabilities')
        .km-title Token Limits
        .row.q-gap-16(v-if='capabilities.max_tokens || capabilities.max_input_tokens || capabilities.max_output_tokens')
          .col(v-if='capabilities.max_input_tokens')
            .km-field.text-secondary-text Max Input Tokens
            .text-body2 {{ capabilities.max_input_tokens?.toLocaleString() }}
          .col(v-if='capabilities.max_output_tokens')
            .km-field.text-secondary-text Max Output Tokens
            .text-body2 {{ capabilities.max_output_tokens?.toLocaleString() }}
          .col(v-if='capabilities.max_tokens && !capabilities.max_input_tokens')
            .km-field.text-secondary-text Max Tokens
            .text-body2 {{ capabilities.max_tokens?.toLocaleString() }}
        .text-secondary-text.km-description(v-else) No token limit information available

        q-separator.q-my-16

        .km-title Capabilities
        .row.q-gap-8.flex-wrap(v-if='hasAnyCapability')
          q-chip(v-if='capabilities.supports_vision', color='primary-light', text-color='primary', size='sm')
            q-icon.q-mr-xs(name='o_visibility', size='14px')
            | Vision
          q-chip(v-if='capabilities.supports_function_calling', color='primary-light', text-color='primary', size='sm')
            q-icon.q-mr-xs(name='o_code', size='14px')
            | Function Calling
          q-chip(v-if='capabilities.supports_response_schema', color='primary-light', text-color='primary', size='sm')
            q-icon.q-mr-xs(name='o_data_object', size='14px')
            | Response Schema
          q-chip(v-if='capabilities.supports_audio_input', color='primary-light', text-color='primary', size='sm')
            q-icon.q-mr-xs(name='o_mic', size='14px')
            | Audio Input
          q-chip(v-if='capabilities.supports_audio_output', color='primary-light', text-color='primary', size='sm')
            q-icon.q-mr-xs(name='o_volume_up', size='14px')
            | Audio Output
        .text-secondary-text.km-description(v-else) No special capabilities detected

        q-separator.q-my-16

        .km-title Provider Pricing
        .row.q-gap-16(v-if='capabilities.input_cost_per_token || capabilities.output_cost_per_token')
          .col(v-if='capabilities.input_cost_per_token')
            .km-field.text-secondary-text Input Cost
            .text-body2 ${{ (capabilities.input_cost_per_token * 1000000).toFixed(4) }} / 1M tokens
          .col(v-if='capabilities.output_cost_per_token')
            .km-field.text-secondary-text Output Cost
            .text-body2 ${{ (capabilities.output_cost_per_token * 1000000).toFixed(4) }} / 1M tokens
        .text-secondary-text.km-description(v-else) No pricing information available from provider

        q-separator.q-my-16

        .km-title Supported Parameters
        .row.q-gap-4.flex-wrap(v-if='capabilities.supported_params?.length')
          q-chip(
            v-for='param in capabilities.supported_params',
            :key='param',
            color='grey-3',
            text-color='grey-8',
            size='sm'
          ) {{ param }}
        .text-secondary-text.km-description(v-else) No supported parameters information available

      template(v-else)
        .text-center.q-pa-lg
          q-icon(name='o_info', size='48px', color='grey-5')
          .text-secondary-text.q-mt-md Model information is not available
          .km-description.text-secondary-text.q-mt-xs Save the model first to load capabilities

  template(#footer)
    .q-pa-16.bt-border
      .row.items-center.q-gap-8
        km-btn(
          flat,
          :label='testingModel ? "Testing..." : "Test Model"',
          :loading='testingModel',
          @click='testModel',
          icon='fas fa-flask',
          color='primary',
          :disable='testingModel || isEntityChanged',
          data-test='TestModel'
        )
        q-space
        km-btn(v-if='isEntityChanged', flat, :label='m.common_cancel()', color='primary', @click='cancelChanges', data-test='Cancel')
        km-btn(v-if='isEntityChanged', :label='m.common_save()', @click='save', data-test='Save')

//- Test Result Dialog
q-dialog(v-model='showTestDialog')
  q-card(style='min-width: 580px; max-width: 720px')
    q-card-section.row.items-center
      .km-heading-7 Test Result
      q-space
      q-btn(icon='close', flat, round, dense, @click='showTestDialog = false')
    q-card-section
      .row.items-center.q-gap-12.q-mb-md
        q-icon(
          :name='testResult?.success ? "fas fa-check-circle" : "fas fa-times-circle"',
          :color='testResult?.success ? "positive" : "negative"',
          size='32px'
        )
        .text-h6(:class='testResult?.success ? "text-positive" : "text-negative"') {{ testResult?.success ? 'Success' : 'Failed' }}
      .km-description.text-secondary-text.q-mb-sm {{ testResult?.message }}
      .q-pa-sm.bg-grey-2.rounded-borders(v-if='testResult?.response_preview')
        .km-field.text-secondary-text.q-mb-xs Response Preview
        .text-body2 {{ testResult?.response_preview }}
      .q-pa-sm.bg-negative-light.rounded-borders.q-mt-sm(v-if='testResult?.error')
        .km-field.text-negative.q-mb-xs Error Details
        .text-body2.text-negative {{ testResult?.error }}

      //- LiteLLM Diagnostic Info
      .q-mt-md.q-pa-sm.bg-grey-2.rounded-borders(
        v-if='testResult?.litellm_model_string || testResult?.effective_endpoint || testResult?.computed_url || testResult?.via_router != null'
      )
        .km-field.text-secondary-text.q-mb-sm Connection Details
        .q-gutter-y-xs
          .row.items-start(v-if='testResult?.litellm_model_string')
            .text-caption.text-grey-7.col-3 Model string
            .text-caption.text-mono.col-9 {{ testResult.litellm_model_string }}
          .row.items-start(v-if='testResult?.effective_endpoint')
            .text-caption.text-grey-7.col-3 Endpoint
            .text-caption.text-mono.col-9(style='word-break: break-all; white-space: normal') {{ testResult.effective_endpoint }}
          .row.items-start(v-if='testResult?.via_router != null')
            .text-caption.text-grey-7.col-3 Via Router
            .col-9
              q-badge(
                :color='testResult.via_router ? "positive" : "grey-6"',
                :label='testResult.via_router ? "Yes" : "No (direct call)"',
                style='font-size: 11px'
              )
          .row.items-start(v-if='testResult?.computed_url')
            .text-caption.text-grey-7.col-3 Request URL
            .text-caption.text-mono.col-9(style='word-break: break-all; white-space: normal') {{ testResult.computed_url }}
    q-card-actions(align='right')
      km-btn(flat, :label='m.common_close()', color='primary', @click='showTestDialog = false')

q-inner-loading(:showing='loading')
</template>
<script>
import { ref, watch, computed, inject } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'
import { getEntityApis } from '@/api'
import { categoryOptions } from '../../config/model/model.js'
import { useEditBufferStore } from '@/stores/editBufferStore'
import { cloneDeep } from 'lodash'
import { notify } from '@shared/utils/notify'

export default {
  setup() {
    const editBuffer = useEditBufferStore()
    const selectedModel = inject('selectedModel')
    const queries = useEntityQueries()
    const { data: listData } = queries.model.useList({ pageSize: 500 })
    const { mutateAsync: updateEntity } = queries.model.useUpdate()
    const { mutateAsync: createEntity } = queries.model.useCreate()
    const items = computed(() => listData.value?.items ?? [])

    const apis = getEntityApis()
    const testModelAction = (id) => apis.model.test(id)
    const capabilitiesAction = (id) => apis.model.capabilities(id)
    const debugInfoAction = (id) => apis.model.debugInfo(id)

    // Buffer key for the currently selected model
    const bufferKey = computed(() => {
      const id = selectedModel.value?.id
      return id ? `modelConfig:${id}` : null
    })

    // Initialize/re-initialize the edit buffer when selectedModel changes
    watch(selectedModel, (newModel) => {
      if (newModel && newModel.id) {
        const key = `modelConfig:${newModel.id}`
        editBuffer.initBuffer(key, 'modelConfig', String(newModel.id), cloneDeep(newModel))
      }
    }, { immediate: true })

    // Draft from edit buffer
    const draft = computed(() => {
      if (!bufferKey.value) return null
      return editBuffer.getDraft(bufferKey.value) ?? null
    })

    // isDirty from edit buffer
    const isDirty = computed(() => {
      if (!bufferKey.value) return false
      return editBuffer.isDirty(bufferKey.value)
    })

    function updateField(key, value) {
      if (!bufferKey.value) return
      editBuffer.updateDraft(bufferKey.value, key, value)
    }

    function revertDraft() {
      if (!bufferKey.value) return
      editBuffer.revertBuffer(bufferKey.value)
    }

    function commitDraft() {
      if (!bufferKey.value) return
      editBuffer.commitBuffer(bufferKey.value)
    }

    return {
      m,
      editBuffer,
      selectedModel,
      bufferKey,
      draft,
      isDirty,
      updateField,
      revertDraft,
      commitDraft,
      tab: ref('parameters'),
      tabs: ref([
        { name: 'parameters', label: 'Parameters' },
        { name: 'pricing', label: 'Pricing' },
        { name: 'routing', label: 'Routing' },
        { name: 'info', label: 'Info' },
      ]),
      priceUnitOptions: ref([
        { label: 'Tokens', value: 'tokens' },
        { label: 'Characters', value: 'characters' },
        { label: 'Queries', value: 'queries' },
      ]),
      categoryOptions,
      loading: ref(false),
      testingModel: ref(false),
      testResult: ref(null),
      showTestDialog: ref(false),
      capabilities: ref(null),
      debugInfo: ref(null),
      items,
      updateEntity,
      createEntity,
      testModelAction,
      capabilitiesAction,
      debugInfoAction,
    }
  },
  computed: {
    modelConfig() {
      return this.draft
    },
    modelId() {
      return this.modelConfig?.id
    },
    isEntityChanged() {
      return this.isDirty
    },
    // Get all models from store for fallback selection
    allModels() {
      return this.items || []
    },
    // Available models for fallback selection (excluding current model)
    availableFallbackModels() {
      const currentSystemName = this.modelConfig?.system_name
      return this.allModels
        .filter(m => m.system_name !== currentSystemName)
        .map(m => ({
          label: `${m.display_name} (${m.provider_system_name || m.provider_name})`,
          value: m.system_name,
        }))
    },
    // Check if model has any special capabilities
    hasAnyCapability() {
      if (!this.capabilities) return false
      return (
        this.capabilities.supports_vision ||
        this.capabilities.supports_function_calling ||
        this.capabilities.supports_response_schema ||
        this.capabilities.supports_audio_input ||
        this.capabilities.supports_audio_output
      )
    },
    display_name: {
      get() {
        return this.modelConfig?.display_name || ''
      },
      set(value) {
        this.updateField('display_name', value)
      },
    },
    description: {
      get() {
        return this.modelConfig?.description || ''
      },
      set(value) {
        this.updateField('description', value)
      },
    },
    system_name: {
      get() {
        return this.modelConfig?.system_name || ''
      },
      set(value) {
        this.updateField('system_name', value)
      },
    },
    provider: {
      get() {
        return this.modelConfig?.provider_name || ''
      },
      set(value) {
        this.updateField('provider_name', value)
      },
    },
    provider_system_name: {
      get() {
        return this.modelConfig?.provider_system_name || ''
      },
      set(value) {
        this.updateField('provider_system_name', value)
      },
    },
    model: {
      get() {
        return this.modelConfig?.ai_model || ''
      },
      set(value) {
        this.updateField('ai_model', value)
      },
    },
    type: {
      get() {
        return this.modelConfig?.type || ''
      },
      set(value) {
        this.updateField('type', value)
      },
    },
    is_default: {
      get() {
        return this.modelConfig?.is_default || false
      },
      set(value) {
        this.updateField('is_default', value)
      },
    },
    json_mode: {
      get() {
        return this.modelConfig?.json_mode || false
      },
      set(value) {
        this.updateField('json_mode', value)
      },
    },
    json_schema: {
      get() {
        return this.modelConfig?.json_schema || false
      },
      set(value) {
        this.updateField('json_schema', value)
      },
    },
    tool_calling: {
      get() {
        return this.modelConfig?.tool_calling || false
      },
      set(value) {
        this.updateField('tool_calling', value)
      },
    },
    reasoning: {
      get() {
        return this.modelConfig?.reasoning || false
      },
      set(value) {
        this.updateField('reasoning', value)
      },
    },
    price_input_unit_name: {
      get() {
        return this.modelConfig?.price_input_unit_name || ''
      },
      set(value) {
        this.updateField('price_input_unit_name', value)
      },
    },
    price_standard_input: {
      get() {
        return this.modelConfig?.price_input || ''
      },
      set(value) {
        this.updateField('price_input', parseFloat(value))
      },
    },
    price_standard_input_unit_count: {
      get() {
        return this.modelConfig?.price_standard_input_unit_count || ''
      },
      set(value) {
        this.updateField('price_standard_input_unit_count', parseFloat(value))
      },
    },
    price_cached_input: {
      get() {
        return this.modelConfig?.price_cached || ''
      },
      set(value) {
        this.updateField('price_cached', parseFloat(value))
      },
    },
    price_cached_input_unit_count: {
      get() {
        return this.modelConfig?.price_cached_input_unit_count || ''
      },
      set(value) {
        this.updateField('price_cached_input_unit_count', parseFloat(value))
      },
    },
    price_output_unit_name: {
      get() {
        return this.modelConfig?.price_output_unit_name || ''
      },
      set(value) {
        this.updateField('price_output_unit_name', value)
      },
    },
    price_standard_output: {
      get() {
        return this.modelConfig?.price_output || ''
      },
      set(value) {
        this.updateField('price_output', parseFloat(value))
      },
    },
    price_standard_output_unit_count: {
      get() {
        return this.modelConfig?.price_standard_output_unit_count || ''
      },
      set(value) {
        this.updateField('price_standard_output_unit_count', parseFloat(value))
      },
    },
    price_reasoning_output: {
      get() {
        return this.modelConfig?.price_reasoning || ''
      },
      set(value) {
        this.updateField('price_reasoning', parseFloat(value) || null)
      },
    },
    price_reasoning_output_unit_count: {
      get() {
        return this.modelConfig?.price_reasoning_output_unit_count || ''
      },
      set(value) {
        this.updateField('price_reasoning_output_unit_count', parseFloat(value) || null)
      },
    },
    is_active: {
      get() {
        return this.modelConfig?.is_active !== false
      },
      set(value) {
        this.updateField('is_active', value)
      },
    },

    resources: {
      get() {
        return this.modelConfig?.resources || ''
      },
      set(value) {
        this.updateField('resources', value)
      },
    },
    vectorSize: {
      get() {
        const configs = this.modelConfig?.configs || {}
        return configs.vector_size || 1536
      },
      set(value) {
        const configs = this.modelConfig?.configs || {}
        const newConfigs = { ...configs, vector_size: parseInt(value) || 1536 }
        this.updateField('configs', newConfigs)
      },
    },
    // Routing Config computed properties
    routingConfig() {
      return this.modelConfig?.routing_config || {}
    },
    cacheEnabled: {
      get() {
        return this.routingConfig?.cache_enabled || false
      },
      set(value) {
        this.updateRoutingConfigProperty('cache_enabled', value)
      },
    },
    cacheTtl: {
      get() {
        return this.routingConfig?.cache_ttl || ''
      },
      set(value) {
        this.updateRoutingConfigProperty('cache_ttl', value ? parseInt(value) : null)
      },
    },
    rpm: {
      get() {
        return this.routingConfig?.rpm || ''
      },
      set(value) {
        this.updateRoutingConfigProperty('rpm', value ? parseInt(value) : null)
      },
    },
    tpm: {
      get() {
        return this.routingConfig?.tpm || ''
      },
      set(value) {
        this.updateRoutingConfigProperty('tpm', value ? parseInt(value) : null)
      },
    },
    numRetries: {
      get() {
        return this.routingConfig?.num_retries ?? ''
      },
      set(value) {
        this.updateRoutingConfigProperty('num_retries', value !== '' ? parseInt(value) : null)
      },
    },
    retryAfter: {
      get() {
        return this.routingConfig?.retry_after ?? ''
      },
      set(value) {
        this.updateRoutingConfigProperty('retry_after', value !== '' ? parseInt(value) : null)
      },
    },
    timeout: {
      get() {
        return this.routingConfig?.timeout || ''
      },
      set(value) {
        this.updateRoutingConfigProperty('timeout', value ? parseInt(value) : null)
      },
    },
    priority: {
      get() {
        return this.routingConfig?.priority || ''
      },
      set(value) {
        this.updateRoutingConfigProperty('priority', value ? parseInt(value) : null)
      },
    },
    weight: {
      get() {
        return this.routingConfig?.weight || ''
      },
      set(value) {
        this.updateRoutingConfigProperty('weight', value ? parseFloat(value) : null)
      },
    },
    fallbackModels: {
      get() {
        const models = this.routingConfig?.fallback_models
        return Array.isArray(models) ? models : []
      },
      set(value) {
        const models = Array.isArray(value) && value.length > 0 ? value : null
        this.updateRoutingConfigProperty('fallback_models', models)
      },
    },
    apiPath: {
      get() {
        return this.routingConfig?.api_path || ''
      },
      set(value) {
        this.updateRoutingConfigProperty('api_path', value || null)
      },
    },
  },
  watch: {
    modelId: {
      immediate: true,
      handler(newId) {
        if (newId) {
          this.fetchCapabilities()
          this.fetchDebugInfo()
        } else {
          this.capabilities = null
          this.debugInfo = null
        }
      },
    },
  },
  methods: {
    updateRoutingConfigProperty(key, value) {
      const currentConfig = this.modelConfig?.routing_config || {}
      const newConfig = { ...currentConfig }
      if (value === null || value === undefined || value === '') {
        delete newConfig[key]
      } else {
        newConfig[key] = value
      }
      // If config is empty, set it to null
      const finalConfig = Object.keys(newConfig).length > 0 ? newConfig : null
      this.updateField('routing_config', finalConfig)
    },
    async save() {
      this.loading = true
      try {
        const entity = this.draft
        if (!entity) throw new Error('No model to save')
        const data = { ...entity }
        const id = data.id
        delete data.id
        delete data.created_at
        delete data.updated_at
        delete data.created_by
        delete data.updated_by
        if (id) {
          await this.updateEntity({ id, data })
        } else {
          await this.createEntity(data)
        }
        this.commitDraft()
        notify.success('Model has been saved.')
      } catch (error) {
        notify.error('Error saving model.')
      } finally {
        this.loading = false
      }
    },
    async testModel() {
      const modelId = this.modelConfig?.id
      if (!modelId) {
        notify.warning('Please save the model first before testing.')
        return
      }

      this.testingModel = true
      this.testResult = null

      try {
        const result = await this.testModelAction(modelId)
        this.testResult = result
        this.showTestDialog = true
      } catch (error) {

        this.testResult = {
          success: false,
          message: 'Failed to test model',
          error: error?.text || error?.message || 'Unknown error',
        }
        this.showTestDialog = true
      } finally {
        this.testingModel = false
      }
    },
    cancelChanges() {
      this.revertDraft()
    },
    goToDefaultModels() {
      this.$router.push({ name: 'ModelProviders', query: { tab: 'DefaultModels' } })
    },
    async fetchDebugInfo() {
      const modelId = this.modelId
      if (!modelId) {
        this.debugInfo = null
        return
      }
      try {
        const result = await this.debugInfoAction(modelId)
        this.debugInfo = result
      } catch {
        this.debugInfo = null
      }
    },
    async fetchCapabilities() {
      const modelId = this.modelId
      if (!modelId) {
        this.capabilities = null
        return
      }

      try {
        const result = await this.capabilitiesAction(modelId)
        this.capabilities = result
      } catch (error) {

        this.capabilities = null
      }
    },
  },
}
</script>