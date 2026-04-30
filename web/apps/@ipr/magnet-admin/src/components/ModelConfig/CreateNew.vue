<template>
  <km-popup-confirm :visible="showNewDialog" :title="popupName" :confirm-button-label="confirmLabel" :cancel-button-label="cancelLabel" notification="You will be able to edit these and other settings after saving." @confirm="confirm" @cancel="cancel">
    <km-stepper v-if="steps?.length &gt; 1" class="full-width" :steps="steps" :stepper="stepper" />
    <template v-if="stepper == 0">
      <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
        Provider
        <km-select ref="providerRef" v-model="selectedProviderId" height="auto" min-height="30px" :placeholder="m.common_provider()" :options="providerOptions" :rules="config.provider.rules" emit-value map-options option-value="value" />
      </div>
      <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
        Provider model name
        <div class="full-width">
          <km-input ref="modelRef" v-model="model" height="30px" :placeholder="m.placeholder_exampleModelId()" :rules="config.model.rules" />
          <div class="km-description text-secondary-text">Name used by the provider to identify the model</div>
        </div>
      </div>
      <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
        System name
        <div class="full-width">
          <km-input ref="system_nameRef" v-model="system_name" height="30px" :placeholder="m.placeholder_exampleModelSystemName()" :rules="config.system_name.rules" />
          <div class="km-description text-secondary-text">System name serves as a unique ID</div>
        </div>
      </div>
      <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
        Display name
        <div class="full-width">
          <km-input ref="display_nameRef" v-model="newRow.display_name" height="30px" :placeholder="m.placeholder_exampleModelName()" :rules="config.display_name.rules" />
          <div class="km-description text-secondary-text">How the model name is displayed</div>
        </div>
      </div>
    </template>
    <template v-if="stepper == 1"> 
      <div v-if="type === &quot;prompts&quot;">
        <div class="km-title mb-md">Structured outputs</div>
        <div class="cluster">
          <km-toggle ref="json_modeRef" v-model="newRow.json_mode" height="30px" :placeholder="m.placeholder_exampleModelName()" :rules="config.json_mode.rules" />
          <div class="km-field text-secondary-text">Supports JSON mode</div>
        </div>
        <div class="cluster">
          <km-toggle ref="json_schemaRef" v-model="newRow.json_schema" height="30px" :placeholder="m.placeholder_exampleModelName()" :rules="config.json_schema.rules" />
          <div class="km-field text-secondary-text">Supports JSON schema</div>
        </div>
        <km-separator class="my-md" />
        <div class="km-title mb-md">Tool calling</div>
        <div class="cluster">
          <km-toggle ref="json_modeRef" v-model="newRow.tool_calling" height="30px" :placeholder="m.placeholder_exampleModelName()" :rules="config.json_mode.rules" />
          <div class="km-field text-secondary-text">Tool calling</div>
        </div>
        <km-separator class="my-md" />
        <div class="km-title mb-md">Reasoning</div>
        <div class="cluster">
          <km-toggle ref="json_modeRef" v-model="newRow.reasoning" height="30px" :placeholder="m.placeholder_exampleModelName()" :rules="config.json_mode.rules" />
          <div class="km-field text-secondary-text">Reasoning</div>
        </div>
      </div>
      <div v-if="type === &quot;embeddings&quot;">
        <div class="km-title mb-md">Vector Configuration</div>
        <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
          Vector Size
          <div class="full-width">
            <km-input ref="vectorSizeRef" v-model.number="vectorSize" height="30px" :placeholder="m.placeholder_exampleVectorSize()" type="number" />
            <div class="km-description text-secondary-text">Dimension of the embedding vector (default: 1536). Common values: 1536 (ada-002), 1024 (embed-3-small), 3072 (embed-3-large)</div>
          </div>
        </div>
      </div>
    </template>
  </km-popup-confirm>
</template>
<script>
import { ref, reactive, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'
import { cloneDeep } from 'lodash'
import { toUpperCaseWithUnderscores } from '@shared'
import { useEntityConfig } from '@/composables/useEntityConfig'
import { validateRef } from '@/utils/validateRef'

export default {
  props: {
    copy: {
      type: Boolean,
      default: false,
    },
    copyData: {
      type: Object,
      default: null,
    },
    type: {
      type: String,
      default: 'prompts',
    },
    showNewDialog: {
      default: false,
      type: Boolean,
    },
  },
  emits: ['cancel'],
  setup(props) {
    const queries = useEntityQueries()
    const { mutateAsync: createEntity } = queries.model.useCreate()
    const { data: providerData } = queries.provider.useList()

    const providerItems = computed(() => providerData.value?.items ?? [])
    const entityConfig = useEntityConfig('model')
    const config = computed(() => entityConfig.config || {})
    const requiredFields = computed(() => entityConfig.requiredFields || [])

    return {
      m,
      createEntity,
      config,
      requiredFields,
      createNew: ref(false),
      selectedProviderId: ref(null),
      newRow: reactive({
        provider_name: '',
        provider_system_name: '',
        name: '',
        display_name: '',
        description: '',
        system_name: '',
        ai_model: '',
        json_mode: false,
        json_schema: false,
        price_input: '',
        price_output: '',
        price_cached: '',
        resources: '',
        type: props.type,
        tool_calling: false,
        reasoning: false,
        diarization: false,
        configs: {},
      }),
      stepper: ref(0),
      autoChangeCode: ref(true),
      autoChangeDisplayName: ref(true),
      providerItems,
    }
  },
  computed: {
    providerOptions() {
      return (this.providerItems || []).map(p => ({
        label: p.name || p.system_name,
        value: p.id,
      }))
    },
    selectedProvider() {
      if (!this.selectedProviderId) return null
      return (this.providerItems || []).find(p => p.id === this.selectedProviderId) || null
    },
    steps() {
      if (this.type === 'prompts' || this.type === 'embeddings') {
        return [
          { step: 0, description: 'Settings', icon: 'pen' },
          { step: 1, description: this.type === 'prompts' ? 'Capabilities' : 'Configuration', icon: 'circle' },
        ]
      }

      return [{ step: 0, description: 'Settings', icon: 'pen' }]
    },
    cancelLabel() {
      if (this.stepper === 0) {
        return 'Cancel'
      }
      return 'Back'
    },
    confirmLabel() {
      if (this.stepper < this.steps?.length - 1) {
        return 'Next'
      }
      return 'Create'
    },
    popupName() {
      if (this.type === 're-ranking') {
        return 'New Re-ranking Model'
      }

      if (this.type === 'embeddings') {
        return 'New Embedding Model'
      }
      return 'New Prompt Model'
    },
    model: {
      get() {
        return this.newRow?.ai_model || ''
      },
      set(val) {
        this.newRow.ai_model = val
        this.newRow.name = val
        const providerName = this.selectedProvider?.system_name || this.selectedProvider?.name || ''
        if (this.autoChangeCode && this.isMounted && providerName) {
          this.newRow.system_name = toUpperCaseWithUnderscores(providerName + '_' + val)
        }
        if (this.autoChangeDisplayName && this.isMounted && providerName && val) {
          const formattedProviderName = this.formatProviderName(providerName)
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
    currentRaw() {
      return this.copyData
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
  watch: {},
  mounted() {
    if (this.copy) {
      this.newRow = reactive(cloneDeep(this.currentRaw))
      this.newRow.display_name = this.newRow.display_name + '_COPY'
      this.newRow.description = this.newRow.description + '_COPY'
      this.newRow.system_name = this.newRow.system_name + '_COPY'
      delete this.newRow.id
    }

    this.isMounted = true
  },
  beforeUnmount() {
    this.isMounted = false
    this.$emit('cancel')
  },
  methods: {
    confirm() {
      if (this.stepper === this.steps?.length - 1) {
        this.createModel()
      } else {
        if (!this.validateFields()) return
        this.stepper++
      }
    },
    cancel() {
      if (this.stepper === 1) {
        this.stepper = 0
        return
      }
      this.$emit('cancel')
    },
    formatProviderName(name) {
      if (!name) return ''
      return name
        .replace(/_/g, ' ')
        .toLowerCase()
        .split(' ')
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')
    },

    validateFields() {
      const validStates = this.requiredFields.map((field) => validateRef(this.$refs[`${field}Ref`]))
      return !validStates.includes(false)
    },
    async createModel() {
      if (!this.validateFields()) return

      // Set provider fields from selected provider
      if (this.selectedProvider) {
        this.newRow.provider_system_name = this.selectedProvider.system_name
        this.newRow.provider_name = this.selectedProvider.system_name
      }

      // Handle configs - only include if not empty
      const payload = { ...this.newRow }
      if (payload.configs && Object.keys(payload.configs).length === 0) {
        delete payload.configs
      }

      // Clean up empty strings
      if (!payload.description) payload.description = null
      if (!payload.resources) payload.resources = null
      if (!payload.price_input) payload.price_input = null
      if (!payload.price_output) payload.price_output = null
      if (!payload.price_cached) payload.price_cached = null

      await this.createEntity(payload)
      this.$emit('cancel')
    },
  },
}
</script>

