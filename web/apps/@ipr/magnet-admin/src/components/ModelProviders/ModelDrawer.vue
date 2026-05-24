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

      .q-mt-8
        km-checkbox(label='Active', :model-value='is_active', @update:model-value='is_active = $event')
        .km-description.text-secondary-text.q-pl-8.q-pt-xs When disabled, this model will not be available for selection

    //- Capabilities Tab — feature flags + per-type configuration
    .column.q-gap-16.q-pa-16(v-if='tab == "capabilities"')
      // Features section for prompts models
      template(v-if='type === "prompts"')
        q-card.km-capability-card(flat, bordered)
          q-card-section
            .km-title Features
            .km-description.text-secondary-text.q-pb-12 Toggle the capabilities this model supports. These flags drive which options become available in the prompt template UI.
            .column.q-gap-8
              km-checkbox(label='JSON mode', :model-value='json_mode', @update:model-value='json_mode = $event')
              km-checkbox(label='Structured Outputs', :model-value='json_schema', @update:model-value='json_schema = $event')
              km-checkbox(label='Tool calling', :model-value='tool_calling', @update:model-value='tool_calling = $event')
              km-checkbox(label='Reasoning', :model-value='reasoning', @update:model-value='reasoning = $event')

        q-card.km-capability-card(flat, bordered)
          q-card-section
            .km-title Parameters
            .km-description.text-secondary-text.q-pb-12 Toggle which standard sampling parameters this model accepts. Disabled parameters are hidden from the prompt template editor and stripped from outgoing requests.
            .column.q-gap-8
              km-checkbox(label='Temperature', :model-value='supports_temperature', @update:model-value='supports_temperature = $event')
              km-checkbox(label='Top P', :model-value='supports_top_p', @update:model-value='supports_top_p = $event')
              km-checkbox(label='Max tokens', :model-value='supports_max_tokens', @update:model-value='supports_max_tokens = $event')

        q-card.km-capability-card(v-if='reasoning', flat, bordered)
          q-card-section
            .km-title Reasoning Effort Options
            .km-description.text-secondary-text.q-pb-12 Reasoning-effort tokens this model accepts. Type each value and press Enter. Refer to the provider's documentation for valid values. Leave empty to hide the selector in the prompt template UI.
            q-select(
              filled,
              dense,
              multiple,
              use-chips,
              use-input,
              hide-dropdown-icon,
              input-debounce='0',
              new-value-mode='add-unique',
              placeholder='Type a value and press Enter (e.g. minimal, low, medium, high, max)',
              :model-value='reasoning_effort_options',
              @update:model-value='reasoning_effort_options = $event'
            )

      // Vector configuration for embeddings models
      template(v-if='type === "embeddings"')
        q-card.km-capability-card(flat, bordered)
          q-card-section
            .km-title Vector Configuration
            .km-description.text-secondary-text.q-pb-12 Dimension of the embedding vector. Common values: 1536 (ada-002), 1024 (embed-3-small), 3072 (embed-3-large).
            .km-field.text-secondary-text.q-pb-xs.q-pl-8 Vector Size
            km-input(height='32px', type='number', placeholder='E.g. 1536', :model-value='vectorSize', @update:model-value='vectorSize = $event')

      // Features section for stt models
      template(v-if='type === "stt"')
        q-card.km-capability-card(flat, bordered)
          q-card-section
            .km-title Features
            .km-description.text-secondary-text.q-pb-12 Toggle the capabilities this speech-to-text model supports.
            .column.q-gap-8
              km-checkbox(label='Diarization', :model-value='diarization', @update:model-value='diarization = $event')
              km-checkbox(label='Keyterms', :model-value='keyterms', @update:model-value='keyterms = $event')

    .column.q-gap-16.q-pa-16(v-if='tab == "pricing"')
      q-card.km-pricing-card(flat, bordered)
        q-card-section.q-pa-16
          .km-title Input Pricing
          .km-description.text-secondary-text.q-pb-12 Pricing applied to tokens, characters or queries sent to the model.
          .row.items-center.q-gap-8.q-mb-12
            .text-caption.text-secondary-text(style='min-width: 32px') Unit
            km-select(
              height='32px',
              :options='priceUnitOptions',
              :model-value='price_input_unit_name',
              @update:model-value='price_input_unit_name = $event',
              emit-value,
              map-options,
              style='width: 120px'
            )
            .text-caption.text-secondary-text per
            km-input(
              height='32px',
              type='number',
              :model-value='priceInputUnitCount',
              @update:model-value='priceInputUnitCount = $event',
              style='width: 120px'
            )
            .text-caption.text-secondary-text {{ price_input_unit_name }}
          q-separator.q-mb-12
          .column.q-gap-8
            .row.items-center.no-wrap.q-gap-12
              .km-field.text-secondary-text.col Standard
              km-input(
                prefix='$',
                height='32px',
                :model-value='price_standard_input',
                @update:model-value='price_standard_input = $event',
                style='width: 140px'
              )
            .row.items-center.no-wrap.q-gap-12
              .km-field.text-secondary-text.col Cached
              km-input(
                prefix='$',
                height='32px',
                :model-value='price_cached_input',
                @update:model-value='price_cached_input = $event',
                style='width: 140px'
              )

      q-card.km-pricing-card(flat, bordered)
        q-card-section.q-pa-16
          .km-title Output Pricing
          .km-description.text-secondary-text.q-pb-12 Pricing applied to tokens, characters or queries returned by the model.
          .row.items-center.q-gap-8.q-mb-12
            .text-caption.text-secondary-text(style='min-width: 32px') Unit
            km-select(
              height='32px',
              :options='priceUnitOptions',
              :model-value='price_output_unit_name',
              @update:model-value='price_output_unit_name = $event',
              emit-value,
              map-options,
              style='width: 120px'
            )
            .text-caption.text-secondary-text per
            km-input(
              height='32px',
              type='number',
              :model-value='priceOutputUnitCount',
              @update:model-value='priceOutputUnitCount = $event',
              style='width: 120px'
            )
            .text-caption.text-secondary-text {{ price_output_unit_name }}
          q-separator.q-mb-12
          .column.q-gap-8
            .row.items-center.no-wrap.q-gap-12
              .km-field.text-secondary-text.col Standard
              km-input(
                prefix='$',
                height='32px',
                :model-value='price_standard_output',
                @update:model-value='price_standard_output = $event',
                style='width: 140px'
              )

      q-card.km-pricing-card(flat, bordered)
        q-card-section.q-pa-16
          .km-title Long Context Pricing
          .km-description.text-secondary-text.q-pb-12 Some providers charge a different rate when the input exceeds a token threshold. Enable this to override the rates above for long inputs.
          km-checkbox(
            label='Apply different pricing for long inputs',
            :model-value='longContextEnabled',
            @update:model-value='longContextEnabled = $event'
          )
          template(v-if='longContextEnabled')
            q-separator.q-my-16
            .row.items-center.q-gap-8.q-mb-16
              .text-caption.text-secondary-text Threshold
              km-input(
                height='32px',
                type='number',
                placeholder='200000',
                :model-value='price_long_context_threshold',
                @update:model-value='price_long_context_threshold = $event',
                style='width: 120px'
              )
              .text-caption.text-secondary-text tokens
            .km-pricing-subtitle.q-mb-8 Input
            .column.q-gap-8.q-mb-16
              .row.items-center.no-wrap.q-gap-12
                .km-field.text-secondary-text.col Standard
                km-input(
                  prefix='$',
                  height='32px',
                  :model-value='price_long_context_input',
                  @update:model-value='price_long_context_input = $event',
                  style='width: 140px'
                )
              .row.items-center.no-wrap.q-gap-12
                .km-field.text-secondary-text.col Cached
                km-input(
                  prefix='$',
                  height='32px',
                  :model-value='price_long_context_cached',
                  @update:model-value='price_long_context_cached = $event',
                  style='width: 140px'
                )
            .km-pricing-subtitle.q-mb-8 Output
            .column.q-gap-8
              .row.items-center.no-wrap.q-gap-12
                .km-field.text-secondary-text.col Standard
                km-input(
                  prefix='$',
                  height='32px',
                  :model-value='price_long_context_output',
                  @update:model-value='price_long_context_output = $event',
                  style='width: 140px'
                )

    //- Routing Config Tab
    .column.q-gap-16.q-pa-16(v-if='tab == "routing"')
      .km-title Endpoint
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 API Path
        km-input(:model-value='apiPath', @update:model-value='apiPath = $event', placeholder='/v2')
        .km-description.text-secondary-text.q-pl-8.q-pt-xs
          | Path appended to the provider endpoint for this model. Must start with /.
          template(v-if='type === "re-ranking"')
            br
            | Azure AI Foundry rerank paths: /v1 → /v1/rerank, /v2 → /v2/rerank, /providers/cohere/v2 → /providers/cohere/v2/rerank
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Request URL
        .q-pa-xs.bg-grey-2.rounded-borders
          .text-caption.text-mono(style='word-break: break-all; white-space: normal') {{ debugInfo?.computed_url || '—' }}

      q-separator.q-my-16

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
          q-chip(v-for='param in capabilities.supported_params', :key='param', color='grey-3', text-color='grey-8', size='sm') {{ param }}
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
      .q-pa-sm.bg-grey-2.rounded-borders.q-mt-sm(v-if='testResult?.response_audio_base64')
        .km-field.text-secondary-text.q-mb-xs Audio Playback
        audio(
          controls,
          style='width: 100%',
          :src='`data:audio/${testResult.response_audio_format || "mp3"};base64,${testResult.response_audio_base64}`'
        )
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
      km-btn(flat, label='Close', color='primary', @click='showTestDialog = false')

q-inner-loading(:showing='loading')
</template>
<script>
import { ref, watch } from 'vue'
import { useChroma } from '@shared'
import { categoryOptions } from '../../config/model/model.js'
const DEFAULT_PRICE_UNIT_COUNT = 1000000
const DEFAULT_PRICE_UNIT_NAME = 'tokens'
const DEFAULT_LONG_CONTEXT_THRESHOLD = 200000

export default {
  setup() {
    const {
      items,
      update,
      create,
      selectedRow,
      test,
      capabilities: capabilitiesAction,
      debugInfo: debugInfoAction,
      ...useCollection
    } = useChroma('model')

    return {
      tab: ref('parameters'),
      tabs: ref([
        { name: 'parameters', label: 'General' },
        { name: 'capabilities', label: 'Capabilities' },
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
      update,
      create,
      selectedRow,
      useCollection,
      testModelAction: test,
      capabilitiesAction,
      debugInfoAction,
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
        .filter((m) => m.system_name !== currentSystemName)
        .map((m) => ({
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
    diarization: {
      get() {
        return this.modelConfig?.diarization || false
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'diarization', value })
      },
    },
    keyterms: {
      get() {
        return this.modelConfig?.keyterms || false
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'keyterms', value })
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
    supports_temperature: {
      get() {
        return this.modelConfig?.supports_temperature !== false
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'supports_temperature', value })
      },
    },
    supports_top_p: {
      get() {
        return this.modelConfig?.supports_top_p !== false
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'supports_top_p', value })
      },
    },
    supports_max_tokens: {
      get() {
        return this.modelConfig?.supports_max_tokens !== false
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'supports_max_tokens', value })
      },
    },
    reasoning_effort_options: {
      get() {
        return this.modelConfig?.reasoning_effort_options || []
      },
      set(value) {
        let normalized = null
        if (Array.isArray(value)) {
          const seen = []
          for (const raw of value) {
            if (typeof raw !== 'string') continue
            const token = raw.trim()
            if (token && !seen.includes(token)) seen.push(token)
          }
          normalized = seen.length > 0 ? seen : null
        }
        this.$store.commit('modelConfig/updateEntityProperty', {
          key: 'reasoning_effort_options',
          value: normalized,
        })
      },
    },
    price_input_unit_name: {
      get() {
        return this.modelConfig?.price_input_unit_name || DEFAULT_PRICE_UNIT_NAME
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_input_unit_name', value })
      },
    },
    price_standard_input: {
      get() {
        return this.modelConfig?.price_input ?? ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_input', value: this.parsePrice(value) })
      },
    },
    // Standard and cached input share a single unit count (the common case);
    // the setter writes both fields to keep the data model consistent.
    priceInputUnitCount: {
      get() {
        return this.modelConfig?.price_standard_input_unit_count || DEFAULT_PRICE_UNIT_COUNT
      },
      set(value) {
        const parsed = parseInt(value, 10) || DEFAULT_PRICE_UNIT_COUNT
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_standard_input_unit_count', value: parsed })
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_cached_input_unit_count', value: parsed })
      },
    },
    price_cached_input: {
      get() {
        return this.modelConfig?.price_cached ?? ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_cached', value: this.parsePrice(value) })
      },
    },
    price_output_unit_name: {
      get() {
        return this.modelConfig?.price_output_unit_name || DEFAULT_PRICE_UNIT_NAME
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_output_unit_name', value })
      },
    },
    price_standard_output: {
      get() {
        return this.modelConfig?.price_output ?? ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_output', value: this.parsePrice(value) })
      },
    },
    priceOutputUnitCount: {
      get() {
        return this.modelConfig?.price_standard_output_unit_count || DEFAULT_PRICE_UNIT_COUNT
      },
      set(value) {
        const parsed = parseInt(value, 10) || DEFAULT_PRICE_UNIT_COUNT
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_standard_output_unit_count', value: parsed })
      },
    },
    longContextEnabled: {
      get() {
        return this.modelConfig?.price_long_context_threshold != null
      },
      set(enabled) {
        if (enabled) {
          if (this.modelConfig?.price_long_context_threshold == null) {
            this.$store.commit('modelConfig/updateEntityProperty', {
              key: 'price_long_context_threshold',
              value: DEFAULT_LONG_CONTEXT_THRESHOLD,
            })
          }
        } else {
          ;['price_long_context_threshold', 'price_long_context_input', 'price_long_context_cached', 'price_long_context_output'].forEach((key) => {
            this.$store.commit('modelConfig/updateEntityProperty', { key, value: null })
          })
        }
      },
    },
    price_long_context_threshold: {
      get() {
        return this.modelConfig?.price_long_context_threshold ?? ''
      },
      set(value) {
        const parsed = parseInt(value, 10)
        this.$store.commit('modelConfig/updateEntityProperty', {
          key: 'price_long_context_threshold',
          value: Number.isFinite(parsed) ? parsed : null,
        })
      },
    },
    price_long_context_input: {
      get() {
        return this.modelConfig?.price_long_context_input ?? ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_long_context_input', value: this.parsePrice(value) })
      },
    },
    price_long_context_cached: {
      get() {
        return this.modelConfig?.price_long_context_cached ?? ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_long_context_cached', value: this.parsePrice(value) })
      },
    },
    price_long_context_output: {
      get() {
        return this.modelConfig?.price_long_context_output ?? ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_long_context_output', value: this.parsePrice(value) })
      },
    },
    is_active: {
      get() {
        return this.modelConfig?.is_active !== false
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'is_active', value })
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
    parsePrice(value) {
      if (value === '' || value === null || value === undefined) return null
      const parsed = parseFloat(value)
      return Number.isFinite(parsed) ? parsed : null
    },
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
    async fetchDebugInfo() {
      const modelId = this.modelId
      if (!modelId) {
        this.debugInfo = null
        return
      }
      try {
        let result
        if (this.debugInfoAction) {
          result = await this.debugInfoAction(modelId)
        } else {
          result = await this.$store.dispatch('chroma/debugInfo', { payload: modelId, entity: 'model' })
        }
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

<style scoped>
.km-capability-card {
  border-radius: 8px;
  background: #fff;
}
.km-capability-card :deep(.km-title) {
  margin-bottom: 4px;
}
.km-pricing-card {
  border-radius: 8px;
}
.km-pricing-subtitle {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--q-secondary-text, #888);
}
</style>
