<template>
  <km-drawer-layout storage-key="drawer-model-providers-model">
    <template #tabs>
      <div class="pt-lg px-lg">
        <km-tabs v-model="tab" class="full-width" narrow-indicator dense align="left" no-caps content-class="km-tabs">
          <template v-for="t in tabs" :key="t">
            <km-tab :name="t.name" :label="t.label" />
          </template>
          <div class="fit" />
        </km-tabs>
      </div>
    </template>
    <div>
      <div v-if="tab == &quot;parameters&quot;" :inert="modelReadonly" :class="modelReadonly ? 'model-drawer__readonly-zone' : null" class="stack gap-lg p-lg">
        <div class="km-title">General settings</div>
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">Name</div>
          <km-input :model-value="model" @update:model-value="model = $event" />
          <div class="km-description text-secondary-text pl-sm pt-xs">Name used by provider to identify the model</div>
        </div>
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">Display name</div>
          <km-input :model-value="display_name" @update:model-value="display_name = $event" />
          <div class="km-description text-secondary-text pl-sm pt-xs">Internal name used across Magnet AI</div>
        </div>
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">System name</div>
          <km-input :model-value="system_name" readonly />
        </div>
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">Type</div>
          <km-select height="32px" :options="categoryOptions" :model-value="type" emit-value map-options @update:model-value="type = $event" />
        </div>
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">Description</div>
          <km-input :model-value="description" @update:model-value="description = $event" />
        </div>
        <div class="mt-sm">
          <div class="cluster" data-gap="sm">
            <km-checkbox :label="m.modelProviders_defaultModel()" :model-value="is_default" dense disable />
            <km-glyph name="info" size="16px" tone="subtle">
              <km-tooltip class="bg-white block-shadow text-secondary-text km-description" self="top middle" :offset="[-50, -50]">If marked as Default, model will be selected by default on related tools</km-tooltip>
            </km-glyph>
            <div class="q-ml">
              <km-btn flat :label="m.modelProviders_editDefaults()" tone="brand" @click="goToDefaultModels" />
            </div>
          </div>
        </div>
        <div class="mt-sm">
          <km-checkbox :label="m.common_activate()" :model-value="is_active" @update:model-value="is_active = $event" />
          <div class="km-description text-secondary-text pl-sm pt-xs">When disabled, this model will not be available for selection</div>
        </div>
        <km-separator class="my-lg" />
        <!-- Features section for prompts models-->
        <template v-if="type === &quot;prompts&quot;">
          <div class="km-title">Features</div>
          <km-checkbox :label="m.common_jsonMode()" :model-value="json_mode" @update:model-value="json_mode = $event" />
          <km-checkbox :label="m.common_structuredOutputs()" :model-value="json_schema" @update:model-value="json_schema = $event" />
          <km-checkbox :label="m.common_toolCalling()" :model-value="tool_calling" @update:model-value="tool_calling = $event" />
          <km-checkbox :label="m.common_reasoning()" :model-value="reasoning" @update:model-value="reasoning = $event" />
        </template>
        <!-- Vector configuration for embeddings models-->
        <template v-if="type === &quot;embeddings&quot;">
          <div class="km-title">Vector Configuration</div>
          <div>
            <div class="km-field text-secondary-text pb-xs pl-sm">Vector Size</div>
            <km-input height="32px" type="number" :placeholder="m.placeholder_exampleVectorSize()" :model-value="vectorSize" @update:model-value="vectorSize = $event" />
            <div class="km-description text-secondary-text pl-sm pt-xs">Dimension of the embedding vector. Common values: 1536 (ada-002), 1024 (embed-3-small), 3072 (embed-3-large)</div>
          </div>
        </template>
      </div>
      <div v-if="tab == &quot;pricing&quot;" :inert="modelReadonly" :class="modelReadonly ? 'model-drawer__readonly-zone' : null" class="stack p-lg" data-gap="lg">
        <div class="km-title">Inputs</div>
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">Input units</div>
          <km-select height="32px" :options="priceUnitOptions" :model-value="price_input_unit_name" emit-value map-options @update:model-value="price_input_unit_name = $event" />
        </div>
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">Price for standard input</div>
          <div class="cluster" data-gap="sm" data-wrap="no">
            <km-input prefix="$" height="32px" :model-value="price_standard_input" class="model-drawer__price-input" @update:model-value="price_standard_input = $event" />
            <div class="text-secondary-text">per</div>
            <km-input height="32px" :model-value="price_standard_input_unit_count" class="model-drawer__price-input" @update:model-value="price_standard_input_unit_count = $event" />
            <div class="text-secondary-text">{{ price_input_unit_name }}</div>
          </div>
        </div>
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">Price for cached input</div>
          <div class="cluster" data-gap="sm" data-wrap="no">
            <km-input prefix="$" height="32px" :model-value="price_cached_input" class="model-drawer__price-input" @update:model-value="price_cached_input = $event" />
            <div class="text-secondary-text">per</div>
            <km-input height="32px" :model-value="price_cached_input_unit_count" class="model-drawer__price-input" @update:model-value="price_cached_input_unit_count = $event" />
            <div class="text-secondary-text">{{ price_input_unit_name }}</div>
          </div>
        </div>
        <km-separator class="my-lg" />
        <div class="km-title">Outputs</div>
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">Output units</div>
          <km-select height="32px" :options="priceUnitOptions" :model-value="price_output_unit_name" emit-value map-options @update:model-value="price_output_unit_name = $event" />
        </div>
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">Price for standard output</div>
          <div class="cluster" data-gap="sm" data-wrap="no">
            <km-input prefix="$" height="32px" :model-value="price_standard_output" class="model-drawer__price-input" @update:model-value="price_standard_output = $event" />
            <div class="text-secondary-text">per</div>
            <km-input height="32px" :model-value="price_standard_output_unit_count" class="model-drawer__price-input" @update:model-value="price_standard_output_unit_count = $event" />
            <div class="text-secondary-text">{{ price_output_unit_name }}</div>
          </div>
        </div>
        <template v-if="reasoning">
          <km-separator class="my-lg" />
          <div class="km-title">Reasoning Output</div>
          <div>
            <div class="km-field text-secondary-text pb-xs pl-sm">Price for reasoning output</div>
            <div class="cluster" data-gap="sm" data-wrap="no">
              <km-input prefix="$" height="32px" :model-value="price_reasoning_output" class="model-drawer__price-input" @update:model-value="price_reasoning_output = $event" />
              <div class="text-secondary-text">per</div>
              <km-input height="32px" :model-value="price_reasoning_output_unit_count" class="model-drawer__price-input" @update:model-value="price_reasoning_output_unit_count = $event" />
              <div class="text-secondary-text">{{ price_output_unit_name }}</div>
            </div>
          </div>
        </template>
      </div>
      <div v-if="tab == &quot;routing&quot;" :inert="modelReadonly" :class="modelReadonly ? 'model-drawer__readonly-zone' : null" class="stack p-lg" data-gap="lg">
        <div class="km-title">Endpoint</div>
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">API Path</div>
          <km-input :model-value="apiPath" :placeholder="m.placeholder_exampleApiPath()" @update:model-value="apiPath = $event" />
          <div class="km-description text-secondary-text pl-sm pt-xs">
            Path appended to the provider endpoint for this model. Must start with /.
            <template v-if="type === 're-ranking'"><br>Azure AI Foundry rerank paths: /v1 → /v1/rerank, /v2 → /v2/rerank, /providers/cohere/v2 → /providers/cohere/v2/rerank</template>
          </div>
        </div>
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">Request URL</div>
          <div class="p-xs bg-grey-2 rounded-borders">
            <div class="text-caption text-mono model-drawer__url">{{ debugInfo?.computed_url || '—' }}</div>
          </div>
        </div>
        <km-separator class="my-lg" />
        <div class="km-title">Caching</div>
        <km-checkbox :label="m.common_enableResponseCaching()" :model-value="cacheEnabled" @update:model-value="cacheEnabled = $event" />
        <div v-if="cacheEnabled">
          <div class="km-field text-secondary-text pb-xs pl-sm">Cache TTL (seconds)</div>
          <km-input height="32px" type="number" placeholder="3600" :model-value="cacheTtl" @update:model-value="cacheTtl = $event" />
          <div class="km-description text-secondary-text pl-sm pt-xs">How long to cache responses (default: 3600 seconds = 1 hour)</div>
        </div>
        <km-separator class="my-lg" />
        <div class="km-title">Rate Limiting</div>
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">Requests per Minute (RPM)</div>
          <km-input height="32px" type="number" placeholder="60" :model-value="rpm" @update:model-value="rpm = $event" />
          <div class="km-description text-secondary-text pl-sm pt-xs">Maximum requests per minute for this model</div>
        </div>
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">Tokens per Minute (TPM)</div>
          <km-input height="32px" type="number" placeholder="100000" :model-value="tpm" @update:model-value="tpm = $event" />
          <div class="km-description text-secondary-text pl-sm pt-xs">Maximum tokens per minute for this model</div>
        </div>
        <km-separator class="my-lg" />
        <div class="km-title">Reliability</div>
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">Number of Retries</div>
          <km-input height="32px" type="number" placeholder="0" :model-value="numRetries" @update:model-value="numRetries = $event" />
          <div class="km-description text-secondary-text pl-sm pt-xs">How many times to retry failed requests before fallback</div>
        </div>
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">Retry After (seconds)</div>
          <km-input height="32px" type="number" placeholder="0" :model-value="retryAfter" @update:model-value="retryAfter = $event" />
          <div class="km-description text-secondary-text pl-sm pt-xs">Delay in seconds before retrying a failed request</div>
        </div>
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">Timeout (seconds)</div>
          <km-input height="32px" type="number" placeholder="60" :model-value="timeout" @update:model-value="timeout = $event" />
          <div class="km-description text-secondary-text pl-sm pt-xs">Request timeout in seconds</div>
        </div>
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">Fallback Models</div>
          <km-select height="auto" min-height="32px" multiple use-chips :placeholder="m.modelProviders_selectFallbackModels()" :options="availableFallbackModels" :model-value="fallbackModels" emit-value map-options @update:model-value="fallbackModels = $event" />
          <div class="km-description text-secondary-text pl-sm pt-xs">Models to use as fallbacks when this model fails (can be from any provider)</div>
        </div>
        <km-separator class="my-lg" />
        <div class="km-title">Load Balancing</div>
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">Priority</div>
          <km-input height="32px" type="number" placeholder="1" :model-value="priority" @update:model-value="priority = $event" />
          <div class="km-description text-secondary-text pl-sm pt-xs">Lower priority values are preferred (default: 1)</div>
        </div>
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">Weight</div>
          <km-input height="32px" type="number" placeholder="1" :model-value="weight" @update:model-value="weight = $event" />
          <div class="km-description text-secondary-text pl-sm pt-xs">Weight for load balancing distribution (default: 1)</div>
        </div>
      </div>
      <div v-if="tab == &quot;info&quot;" class="stack p-lg" data-gap="lg">
        <template v-if="capabilities">
          <div class="km-title">Token Limits</div>
          <div v-if="capabilities.max_tokens || capabilities.max_input_tokens || capabilities.max_output_tokens" class="cluster" data-gap="lg">
            <div v-if="capabilities.max_input_tokens" class="flex-1">
              <div class="km-field text-secondary-text">Max Input Tokens</div>
              <div class="text-body2">{{ capabilities.max_input_tokens?.toLocaleString() }}</div>
            </div>
            <div v-if="capabilities.max_output_tokens" class="flex-1">
              <div class="km-field text-secondary-text">Max Output Tokens</div>
              <div class="text-body2">{{ capabilities.max_output_tokens?.toLocaleString() }}</div>
            </div>
            <div v-if="capabilities.max_tokens &amp;&amp; !capabilities.max_input_tokens" class="flex-1">
              <div class="km-field text-secondary-text">Max Tokens</div>
              <div class="text-body2">{{ capabilities.max_tokens?.toLocaleString() }}</div>
            </div>
          </div>
          <div v-else class="text-secondary-text km-description">No token limit information available</div>
          <km-separator class="my-lg" />
          <div class="km-title">Capabilities</div>
          <div v-if="hasAnyCapability" class="cluster" data-gap="sm">
            <km-chip v-if="capabilities.supports_vision" tone="brand" size="sm">
              <km-glyph class="mr-xs" name="o_visibility" size="14px" />Vision
            </km-chip>
            <km-chip v-if="capabilities.supports_function_calling" tone="brand" size="sm">
              <km-glyph class="mr-xs" name="o_code" size="14px" />Function Calling
            </km-chip>
            <km-chip v-if="capabilities.supports_response_schema" tone="brand" size="sm">
              <km-glyph class="mr-xs" name="o_data_object" size="14px" />Response Schema
            </km-chip>
            <km-chip v-if="capabilities.supports_audio_input" tone="brand" size="sm">
              <km-glyph class="mr-xs" name="o_mic" size="14px" />Audio Input
            </km-chip>
            <km-chip v-if="capabilities.supports_audio_output" tone="brand" size="sm">
              <km-glyph class="mr-xs" name="o_volume_up" size="14px" />Audio Output
            </km-chip>
          </div>
          <div v-else class="text-secondary-text km-description">No special capabilities detected</div>
          <km-separator class="my-lg" />
          <div class="km-title">Provider Pricing</div>
          <div v-if="capabilities.input_cost_per_token || capabilities.output_cost_per_token" class="cluster" data-gap="lg">
            <div v-if="capabilities.input_cost_per_token" class="flex-1">
              <div class="km-field text-secondary-text">Input Cost</div>
              <div class="text-body2">${{ (capabilities.input_cost_per_token * 1000000).toFixed(4) }} / 1M tokens</div>
            </div>
            <div v-if="capabilities.output_cost_per_token" class="flex-1">
              <div class="km-field text-secondary-text">Output Cost</div>
              <div class="text-body2">${{ (capabilities.output_cost_per_token * 1000000).toFixed(4) }} / 1M tokens</div>
            </div>
          </div>
          <div v-else class="text-secondary-text km-description">No pricing information available from provider</div>
          <km-separator class="my-lg" />
          <div class="km-title">Supported Parameters</div>
          <div v-if="capabilities.supported_params?.length" class="cluster" data-gap="xs">
            <km-chip v-for="param in capabilities.supported_params" :key="param" tone="neutral" size="sm">{{ param }}</km-chip>
          </div>
          <div v-else class="text-secondary-text km-description">No supported parameters information available</div>
        </template>
        <template v-else>
          <div class="text-center p-lg">
            <km-glyph name="info" size="48px" tone="muted" />
            <div class="text-secondary-text mt-md">Model information is not available</div>
            <div class="km-description text-secondary-text mt-xs">Save the model first to load capabilities</div>
          </div>
        </template>
      </div>
    </div>
    <template #footer>
      <div class="cluster" data-gap="sm">
        <km-btn flat :label="testingModel ? &quot;Testing...&quot; : &quot;Test Model&quot;" :loading="testingModel" icon="flask" tone="brand" :disable="testingModel || isEntityChanged" data-test="TestModel" @click="testModel" />
        <div class="km-space" />
        <km-btn v-if="!modelReadonly && isEntityChanged" flat :label="m.common_cancel()" tone="brand" data-test="Cancel" @click="cancelChanges" />
        <km-btn v-if="!modelReadonly && isEntityChanged" :label="m.common_save()" data-test="Save" @click="save" />
      </div>
    </template>
  </km-drawer-layout>
  <km-dialog v-model="showTestDialog">
    <km-card class="model-drawer__card">
      <div class="km-card-section cluster">
        <div class="km-heading-7">Test Result</div>
        <div class="km-space" />
        <km-btn icon="close" flat round dense @click="showTestDialog = false" />
      </div>
      <div class="km-card-section">
        <div class="cluster" data-gap="md">
          <km-glyph :name="testResult?.success ? &quot;check&quot; : &quot;error&quot;" :tone="testResult?.success ? &quot;success&quot; : &quot;danger&quot;" size="32px" />
          <div class="text-h6" :class="testResult?.success ? &quot;text-positive&quot; : &quot;text-negative&quot;">{{ testResult?.success ? 'Success' : 'Failed' }}</div>
        </div>
        <div class="km-description text-secondary-text mb-sm">{{ testResult?.message }}</div>
        <div v-if="testResult?.response_preview" class="p-sm bg-grey-2 rounded-borders">
          <div class="km-field text-secondary-text mb-xs">Response Preview</div>
          <div class="text-body2">{{ testResult?.response_preview }}</div>
        </div>
        <div v-if="testResult?.error" class="p-sm bg-negative-light rounded-borders mt-sm">
          <div class="km-field text-negative mb-xs">Error Details</div>
          <div class="text-body2 text-negative">{{ testResult?.error }}</div>
        </div>
        <div v-if="testResult?.litellm_model_string || testResult?.effective_endpoint || testResult?.computed_url || testResult?.via_router != null" class="mt-md p-sm bg-grey-2 rounded-borders">
          <div class="km-field text-secondary-text mb-sm">Connection Details</div>
          <div class="gap-y-xs">
            <div v-if="testResult?.litellm_model_string" class="cluster" data-align="start">
              <div class="text-caption text-grey-7 basis-3">Model string</div>
              <div class="text-caption text-mono basis-9">{{ testResult.litellm_model_string }}</div>
            </div>
            <div v-if="testResult?.effective_endpoint" class="cluster" data-align="start">
              <div class="text-caption text-grey-7 basis-3">Endpoint</div>
              <div class="text-caption text-mono basis-9 model-drawer__url">{{ testResult.effective_endpoint }}</div>
            </div>
            <div v-if="testResult?.via_router != null" class="cluster" data-align="start">
              <div class="text-caption text-grey-7 basis-3">Via Router</div>
              <div class="basis-9">
                <km-badge :tone="testResult.via_router ? &quot;success&quot; : &quot;neutral&quot;" :label="testResult.via_router ? &quot;Yes&quot; : &quot;No (direct call)&quot;" class="model-drawer__badge-xs" />
              </div>
            </div>
            <div v-if="testResult?.computed_url" class="cluster" data-align="start">
              <div class="text-caption text-grey-7 basis-3">Request URL</div>
              <div class="text-caption text-mono basis-9 model-drawer__url">{{ testResult.computed_url }}</div>
            </div>
          </div>
        </div>
      </div>
      <div class="km-card-actions" align="right">
        <km-btn flat :label="m.common_close()" tone="brand" @click="showTestDialog = false" />
      </div>
    </km-card>
  </km-dialog>
  <km-inner-loading :showing="loading" />
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
    const modelProviderReadonlyRef = inject('modelProviderReadonly', null)
    const modelReadonly = computed(() => Boolean(modelProviderReadonlyRef?.value))
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
      if (modelReadonly.value) return
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
      modelReadonly,
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
      if (this.modelReadonly) return
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
      if (this.modelReadonly) return
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

<style scoped>
.model-drawer__price-input {
  max-inline-size: 120px;
}

.model-drawer__url {
  word-break: break-all;
  white-space: normal;
}

.model-drawer__card {
  min-inline-size: 580px;
  max-inline-size: 720px;
}

.model-drawer__badge-xs {
  font-size: var(--ds-font-size-xs);
}

.model-drawer__readonly-zone {
  opacity: 0.72;
  cursor: not-allowed;
}

.model-drawer__readonly-zone :where(input, textarea, select, button, [role='button']) {
  cursor: not-allowed;
}
</style>
