<template>
  <km-popup-confirm :visible="showNewDialog" :title="popupTitle" :confirm-button-label="confirmLabel" :cancel-button-label="cancelLabel" notification="You will be able to edit these and other settings after saving." @confirm="confirm" @cancel="cancel">
    <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
      Provider model name
      <div class="full-width">
        <km-input ref="modelRef" v-model="model" height="30px" :placeholder="m.placeholder_exampleModelId()" :rules="config?.model?.rules || []" />
        <div class="km-description text-secondary-text">The exact model name/deployment name used by the provider (case-sensitive)</div>
      </div>
    </div>
    <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
      System name
      <div class="full-width">
        <km-input ref="system_nameRef" v-model="system_name" height="30px" :placeholder="m.placeholder_exampleModelSystemName()" :rules="config?.system_name?.rules || []" />
        <div class="km-description text-secondary-text">System name serves as a unique ID (auto-generated)</div>
      </div>
    </div>
    <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
      Display name
      <div class="full-width">
        <km-input ref="display_nameRef" v-model="display_name" height="30px" :placeholder="m.placeholder_exampleModelName()" :rules="config?.display_name?.rules || []" />
        <div class="km-description text-secondary-text">How the model name is displayed in the UI</div>
      </div>
    </div>
    <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
      Type
      <div class="full-width">
        <km-select ref="typeRef" v-model="newRow.type" height="auto" min-height="30px" :placeholder="m.common_type()" :options="categoryOptions" :rules="config?.type?.rules || []" emit-value map-options />
        <div class="km-description text-secondary-text">{{ typeDescription }}</div>
      </div>
    </div>
    <template v-if="newRow.type === &quot;prompts&quot;">
      <div class="km-field text-secondary-text pb-xs pl-sm mb-sm">Features</div>
      <div class="cluster px-sm mb-md" data-gap="md">
        <div class="basis-6">
          <km-checkbox v-model="newRow.json_mode" :label="m.common_jsonMode()" dense />
        </div>
        <div class="basis-6">
          <km-checkbox v-model="newRow.json_schema" :label="m.common_structuredOutput()" dense />
        </div>
        <div class="basis-6">
          <km-checkbox v-model="newRow.tool_calling" :label="m.common_toolCalling()" dense />
        </div>
        <div class="basis-6">
          <km-checkbox v-model="newRow.reasoning" :label="m.common_reasoning()" dense />
        </div>
      </div>
    </template>
    <template v-if="newRow.type === &quot;embeddings&quot;">
      <div class="km-field text-secondary-text pb-xs pl-sm mb-md">Vector Size</div>
      <div class="full-width">
        <km-input ref="vectorSizeRef" v-model="vectorSize" height="30px" type="number" :placeholder="m.placeholder_exampleVectorSize()" />
        <div class="km-description text-secondary-text">Dimension of the embedding vector</div>
      </div>
    </template>
    <template v-if="newRow.type === &quot;stt&quot;">
      <div class="km-field text-secondary-text pb-xs pl-sm mb-sm">Features</div>
      <div class="cluster px-sm mb-md" data-gap="md">
        <div class="basis-6">
          <km-checkbox v-model="newRow.diarization" :label="m.noteTaker_diarization()" dense />
        </div>
      </div>
    </template>
  </km-popup-confirm>
</template>

<script>
import { ref, reactive } from 'vue'
import { m } from '@/paraglide/messages'
import { toUpperCaseWithUnderscores } from '@shared'
import { useEntityConfig } from '@/composables/useEntityConfig'
import { validateRef } from '@/utils/validateRef'
import { useEntityQueries } from '@/queries/entities'
import { getEntityApis } from '@/api'
import { categoryOptions } from '../../config/model/model.js'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useSafeMutation } from '@/composables/useSafeMutation'

export default {
  props: {
    showNewDialog: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['cancel'],
  setup() {
    const { config, requiredFields } = useEntityConfig('model')
    const queries = useEntityQueries()
    const { draft: providerDraft } = useEntityDetail('provider')
    const createModelMutation = useSafeMutation(queries.model.useCreate())

    return {
      m,
      providerDraft,
      config,
      createModelMutation,
      requiredFields,
      autoChangeCode: ref(true),
      autoChangeDisplayName: ref(true),
      categoryOptions,
      newRow: reactive({
        name: '',
        provider_name: '',
        provider_system_name: '',
        ai_model: '',
        system_name: '',
        display_name: '',
        type: 'prompts',
        json_mode: false,
        json_schema: false,
        tool_calling: false,
        reasoning: false,
        diarization: false,
        price_input: '',
        price_output: '',
        price_cached: '',
        resources: '',
        description: '',
        configs: {},
      }),
    }
  },
  data() {
    return {
      isMounted: false,
      availableModels: [],
    }
  },
  computed: {
    provider() {
      return this.providerDraft
    },
    cancelLabel() {
      return 'Cancel'
    },
    confirmLabel() {
      return 'Create'
    },
    popupTitle() {
      return 'New Model'
    },
    typeDescription() {
      const type = this.newRow?.type
      const descriptions = {
        prompts: 'Chat completion models for generating text responses (e.g., GPT-4, Claude)',
        embeddings: 'Vector embedding models for text similarity and search (e.g., text-embedding-ada-002)',
        're-ranking': 'Re-ranking models for improving search result relevance',
      }
      return descriptions[type] || 'Select the type of model based on its purpose'
    },
    model: {
      get() {
        return this.newRow?.ai_model || ''
      },
      set(val) {
        this.newRow.ai_model = val
        this.newRow.name = val

        // Auto-detect capabilities
        this.checkModelCapabilities(val)

        if (this.autoChangeCode && this.isMounted && this.provider?.system_name) {
          this.newRow.system_name = toUpperCaseWithUnderscores(this.provider.system_name + '_' + val)
        }
        if (this.autoChangeDisplayName && this.isMounted && this.provider?.name && val) {
          const formattedProviderName = this.formatProviderName(this.provider.name)
          this.newRow.display_name = `${formattedProviderName}: ${val}`
        }
      },
    },
    system_name: {
      get() {
        return this.newRow?.system_name || ''
      },
      set(val) {
        this.newRow.system_name = val
        this.autoChangeCode = false
      },
    },
    display_name: {
      get() {
        return this.newRow?.display_name || ''
      },
      set(val) {
        this.newRow.display_name = val
        this.autoChangeDisplayName = false
      },
    },
    vectorSize: {
      get() {
        return this.newRow?.configs?.vector_size || 1536
      },
      set(val) {
        if (!this.newRow.configs) {
          this.newRow.configs = {}
        }
        this.newRow.configs.vector_size = parseInt(val) || 1536
      },
    },
  },
  mounted() {
    if (this.provider?.system_name) {
      this.newRow.provider_system_name = this.provider.system_name
      this.newRow.provider_name = this.provider.system_name
    }
    this.isMounted = true
    
    // Fetch available models for auto-detection
    if (this.provider?.id) {
       const apis = getEntityApis()
       apis.provider.availableModels(this.provider.id).then(result => {
         if (result && result.models) {
           this.availableModels = result.models
         }
       }).catch(() => {})
    }
  },
  beforeUnmount() {
    this.isMounted = false
  },
  methods: {
    checkModelCapabilities(modelName) {
      if (!modelName || !this.availableModels || !this.availableModels.length) return
      
      const found = this.availableModels.find(m => m.id === modelName)
      if (found && this.newRow.type === 'prompts') {
        this.newRow.json_mode = found.supports_json_mode || false
        this.newRow.json_schema = found.supports_response_schema || false
        this.newRow.tool_calling = found.supports_function_calling || false
        // reasoning is not typically returned by litellm yet, but if it is:
        if (found.supports_reasoning !== undefined) {
          this.newRow.reasoning = found.supports_reasoning
        }
      }
    },
    formatProviderName(name) {
      if (!name) return ''
      // Replace underscores with spaces and convert to proper case
      return name
        .replace(/_/g, ' ')
        .toLowerCase()
        .split(' ')
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')
    },
    confirm() {
      this.createModel()
    },
    cancel() {
      this.$emit('cancel')
    },
    validateFields() {
      if (!this.requiredFields || !Array.isArray(this.requiredFields)) {
        return true
      }
      const validStates = this.requiredFields.map((field) => validateRef(this.$refs[`${field}Ref`]))
      return !validStates.includes(false)
    },
    async createModel() {
      if (!this.validateFields()) return

      // Ensure provider is set
      if (this.provider?.system_name) {
        this.newRow.provider_system_name = this.provider.system_name
        this.newRow.provider_name = this.provider.system_name
      }

      // Clean up empty strings - convert to null or remove
      const payload = { ...this.newRow }
      if (!payload.provider_system_name) {
        delete payload.provider_system_name
      }
      if (!payload.description) {
        payload.description = null
      }
      if (!payload.resources) {
        payload.resources = null
      }
      if (!payload.price_input) {
        payload.price_input = null
      }
      if (!payload.price_output) {
        payload.price_output = null
      }
      if (!payload.price_cached) {
        payload.price_cached = null
      }

      // Handle configs - only include if not empty
      if (payload.configs && Object.keys(payload.configs).length === 0) {
        delete payload.configs
      }

      const { success } = await this.createModelMutation.run(payload)
      if (!success) return
      this.$emit('cancel')
    },
  },
}
</script>

