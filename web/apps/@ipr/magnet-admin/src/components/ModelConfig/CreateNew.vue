<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  :title='popupName',
  :confirmButtonLabel='confirmLabel',
  :cancelButtonLabel='cancelLabel',
  notification='You will be able to edit these and other settings after saving.',
  @confirm='confirm',
  @cancel='cancel'
)
  km-stepper.full-width(v-if='steps?.length > 1', :steps='steps', :stepper='stepper')
  template(v-if='stepper == 0')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Provider
      |
      km-select(
        height='auto',
        minHeight='30px',
        placeholder='Provider',
        :options='providerOptions',
        v-model='selectedProviderId',
        ref='providerRef',
        :rules='config.provider.rules',
        emit-value,
        map-options,
        option-value='value'
      )
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Provider model name
      .full-width
        km-input(height='30px', placeholder='E.g. gpt-4o-mini', v-model='model', ref='modelRef', :rules='config.model.rules')
        .km-description.text-secondary-text Name used by the provider to identify the model
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md System name
      .full-width
        km-input(height='30px', placeholder='E.g. GPT-4O-MINI', v-model='system_name', ref='system_nameRef', :rules='config.system_name.rules')
        .km-description.text-secondary-text System name serves as a unique ID

    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Display name
      .full-width
        km-input(
          height='30px',
          placeholder='E.g. GPT 4o mini',
          v-model='newRow.display_name',
          ref='display_nameRef',
          :rules='config.display_name.rules'
        )
        .km-description.text-secondary-text How the model name is displayed

  template(v-if='stepper == 1') 
    div(v-if='type === "prompts"')
      .km-title.q-mb-md Structured outputs
      .row.items-center
        q-toggle(height='30px', placeholder='E.g. GPT 4o mini', v-model='newRow.json_mode', ref='json_modeRef', :rules='config.json_mode.rules')
        .km-field.text-secondary-text Supports JSON mode
      .row.items-center
        q-toggle(
          height='30px',
          placeholder='E.g. GPT 4o mini',
          v-model='newRow.json_schema',
          ref='json_schemaRef',
          :rules='config.json_schema.rules'
        )
        .km-field.text-secondary-text Supports JSON schema

      q-separator.q-my-md
      .km-title.q-mb-md Tool calling
      .row.items-center
        q-toggle(height='30px', placeholder='E.g. GPT 4o mini', v-model='newRow.tool_calling', ref='json_modeRef', :rules='config.json_mode.rules')
        .km-field.text-secondary-text Tool calling
      q-separator.q-my-md
      .km-title.q-mb-md Reasoning
      .row.items-center
        q-toggle(height='30px', placeholder='E.g. GPT 4o mini', v-model='newRow.reasoning', ref='json_modeRef', :rules='config.json_mode.rules')
        .km-field.text-secondary-text Reasoning

    div(v-if='type === "embeddings"')
      .km-title.q-mb-md Vector Configuration
      .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Vector Size
        .full-width
          km-input(height='30px', placeholder='E.g. 1536', v-model.number='vectorSize', ref='vectorSizeRef', type='number')
          .km-description.text-secondary-text Dimension of the embedding vector (default: 1536). Common values: 1536 (ada-002), 1024 (embed-3-small), 3072 (embed-3-large)
</template>
<script>
import { ref, reactive, computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { cloneDeep } from 'lodash'
import { toUpperCaseWithUnderscores } from '@shared'
import { useModelConfigDetailStore } from '@/stores/entityDetailStores'
import { useEntityConfig } from '@/composables/useEntityConfig'

export default {
  props: {
    copy: {
      type: Boolean,
      default: false,
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
    const modelConfigStore = useModelConfigDetailStore()
    const queries = useEntityQueries()
    const { mutateAsync: createEntity } = queries.model.useCreate()
    const { data: providerData } = queries.provider.useList()

    const providerItems = computed(() => providerData.value?.items ?? [])
    const entityConfig = useEntityConfig('model')
    const config = computed(() => entityConfig.config || {})
    const requiredFields = computed(() => entityConfig.requiredFields || [])

    return {
      modelConfigStore,
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
      return this.modelConfigStore.entity
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
      const validStates = this.requiredFields.map((field) => this.$refs[`${field}Ref`]?.validate())
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

<style lang="stylus">
.km-input:not(.q-field--readonly) .q-field__control::before
  background: var(--q-white) !important;
</style>
