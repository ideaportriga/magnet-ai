<template lang="pug">
.column.bg-white.fit.bl-border.height-100.fit(style='min-width: 500px; max-width: 500px')
  .col-auto.q-pt-16.q-px-16
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
  .col.overflow-auto
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
          km-checkbox(label='Default Model', :model-value='is_default', dense, disable)
          q-icon(name='o_info', size='16px', color='secondary-text')
            q-tooltip.bg-white.block-shadow.text-secondary-text.km-description(self='top middle', :offset='[-50, -50]') If marked as Default, model will be selected by default on related tools
          .q-ml
            km-btn(flat, label='Edit defaults', color='primary', @click='goToDefaultModels')

      q-separator.q-my-16

      // Features section for prompts models
      template(v-if='type === "prompts"')
        .km-title Features
        km-checkbox(label='JSON mode', :model-value='json_mode', @update:model-value='json_mode = $event')
        km-checkbox(label='Structured Outputs', :model-value='json_schema', @update:model-value='json_schema = $event')
        km-checkbox(label='Tool calling', :model-value='tool_calling', @update:model-value='tool_calling = $event')
        km-checkbox(label='Reasoning', :model-value='reasoning', @update:model-value='reasoning = $event')

      // Vector configuration for embeddings models
      template(v-if='type === "embeddings"')
        .km-title Vector Configuration
        div
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Vector Size
          km-input(height='32px', type='number', placeholder='E.g. 1536', :model-value='vectorSize', @update:model-value='vectorSize = $event')
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
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Price for cached output
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
      .km-title Caching
      km-checkbox(label='Enable Response Caching', :model-value='cacheEnabled', @update:model-value='cacheEnabled = $event')
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
        km-input(height='32px', type='number', placeholder='3', :model-value='numRetries', @update:model-value='numRetries = $event')
        .km-description.text-secondary-text.q-pl-8.q-pt-xs How many times to retry failed requests
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
          placeholder='Select fallback models',
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

  .col-auto.q-pa-16
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
      km-btn(v-if='isEntityChanged', flat, label='Cancel', color='primary', @click='cancelChanges', data-test='Cancel')
      km-btn(v-if='isEntityChanged', label='Save', @click='save', data-test='Save')

//- Test Result Dialog
q-dialog(v-model='showTestDialog')
  q-card(style='min-width: 400px; max-width: 500px')
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
    q-card-actions(align='right')
      km-btn(flat, label='Close', color='primary', @click='showTestDialog = false')

q-inner-loading(:showing='loading')
</template>
<script>
import { ref, watch } from 'vue'
import { useChroma } from '@shared'
import { categoryOptions } from '../../config/model/model.js'

export default {
  setup() {
    const { items, update, create, selectedRow, test, capabilities: capabilitiesAction, ...useCollection } = useChroma('model')

    return {
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
      items,
      update,
      create,
      selectedRow,
      useCollection,
      testModelAction: test,
      capabilitiesAction,
    }
  },
  computed: {
    modelConfig() {
      return this.$store.getters['modelConfig/entity']
    },
    modelId() {
      return this.modelConfig?.id
    },
    isEntityChanged() {
      return this.$store.getters['modelConfig/isEntityChanged']
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
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'display_name', value })
      },
    },
    description: {
      get() {
        return this.modelConfig?.description || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'description', value })
      },
    },
    system_name: {
      get() {
        return this.modelConfig?.system_name || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'system_name', value })
      },
    },
    provider: {
      get() {
        return this.modelConfig?.provider_name || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'provider_name', value })
      },
    },
    provider_system_name: {
      get() {
        return this.modelConfig?.provider_system_name || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'provider_system_name', value })
      },
    },
    model: {
      get() {
        return this.modelConfig?.ai_model || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'ai_model', value })
      },
    },
    type: {
      get() {
        return this.modelConfig?.type || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'type', value })
      },
    },
    is_default: {
      get() {
        return this.modelConfig?.is_default || false
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'is_default', value })
      },
    },
    json_mode: {
      get() {
        return this.modelConfig?.json_mode || false
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'json_mode', value })
      },
    },
    json_schema: {
      get() {
        return this.modelConfig?.json_schema || false
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'json_schema', value })
      },
    },
    tool_calling: {
      get() {
        return this.modelConfig?.tool_calling || false
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'tool_calling', value })
      },
    },
    reasoning: {
      get() {
        return this.modelConfig?.reasoning || false
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'reasoning', value })
      },
    },
    price_input_unit_name: {
      get() {
        return this.modelConfig?.price_input_unit_name || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_input_unit_name', value })
      },
    },
    price_standard_input: {
      get() {
        return this.modelConfig?.price_input || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_input', value: parseFloat(value) })
      },
    },
    price_standard_input_unit_count: {
      get() {
        return this.modelConfig?.price_standard_input_unit_count || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_standard_input_unit_count', value: parseFloat(value) })
      },
    },
    price_cached_input: {
      get() {
        return this.modelConfig?.price_cached || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_cached', value: parseFloat(value) })
      },
    },
    price_cached_input_unit_count: {
      get() {
        return this.modelConfig?.price_cached_input_unit_count || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_cached_input_unit_count', value: parseFloat(value) })
      },
    },
    price_output_unit_name: {
      get() {
        return this.modelConfig?.price_output_unit_name || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_output_unit_name', value })
      },
    },
    price_standard_output: {
      get() {
        return this.modelConfig?.price_output || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_output', value: parseFloat(value) })
      },
    },
    price_standard_output_unit_count: {
      get() {
        return this.modelConfig?.price_standard_output_unit_count || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_standard_output_unit_count', value: parseFloat(value) })
      },
    },
    price_reasoning_output: {
      get() {
        return this.modelConfig?.price_reasoning || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_reasoning', value: parseFloat(value) })
      },
    },
    price_reasoning_output_unit_count: {
      get() {
        return this.modelConfig?.price_reasoning_output_unit_count || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_reasoning_output_unit_count', value: parseFloat(value) })
      },
    },
    resources: {
      get() {
        return this.modelConfig?.resources || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'resources', value })
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
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'configs', value: newConfigs })
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
        return this.routingConfig?.num_retries || ''
      },
      set(value) {
        this.updateRoutingConfigProperty('num_retries', value ? parseInt(value) : null)
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
  },
  watch: {
    modelId: {
      immediate: true,
      handler(newId) {
        if (newId) {
          this.fetchCapabilities()
        } else {
          this.capabilities = null
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
      this.$store.commit('modelConfig/updateEntityProperty', { key: 'routing_config', value: finalConfig })
    },
    async save() {
      this.loading = true
      try {
        await this.$store.dispatch('modelConfig/saveEntity')
        this.$q.notify({
          position: 'top',
          message: 'Model has been saved.',
          color: 'positive',
          textColor: 'black',
          timeout: 1000,
        })
      } catch (error) {
        console.error('Error saving model:', error)
        this.$q.notify({
          position: 'top',
          message: 'Error saving model.',
          color: 'negative',
          textColor: 'white',
          timeout: 2000,
        })
      } finally {
        this.loading = false
      }
    },
    async testModel() {
      const modelId = this.modelConfig?.id
      if (!modelId) {
        this.$q.notify({
          position: 'top',
          message: 'Please save the model first before testing.',
          color: 'warning',
          textColor: 'black',
          timeout: 2000,
        })
        return
      }

      this.testingModel = true
      this.testResult = null

      try {
        // Use store dispatch directly if testModelAction is not available
        let result
        if (this.testModelAction) {
          result = await this.testModelAction(modelId)
        } else {
          result = await this.$store.dispatch('chroma/test', { payload: modelId, entity: 'model' })
        }
        this.testResult = result
        this.showTestDialog = true
      } catch (error) {
        console.error('Error testing model:', error)
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
      this.$store.commit('modelConfig/revertEntity')
    },
    goToDefaultModels() {
      this.$router.push({ name: 'ModelProviders', query: { tab: 'DefaultModels' } })
    },
    async fetchCapabilities() {
      const modelId = this.modelId
      if (!modelId) {
        this.capabilities = null
        return
      }

      try {
        let result
        if (this.capabilitiesAction) {
          result = await this.capabilitiesAction(modelId)
        } else {
          result = await this.$store.dispatch('chroma/capabilities', { payload: modelId, entity: 'model' })
        }
        this.capabilities = result
      } catch (error) {
        console.error('Error fetching model capabilities:', error)
        this.capabilities = null
      }
    },
  },
}
</script>