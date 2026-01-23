<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  :title='popupTitle',
  :confirmButtonLabel='confirmLabel',
  :cancelButtonLabel='cancelLabel',
  notification='You will be able to edit these and other settings after saving.',
  @confirm='confirm',
  @cancel='cancel'
)
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Provider model name
    .full-width
      km-input(height='30px', placeholder='E.g. gpt-4o-mini', v-model='model', ref='modelRef', :rules='config?.model?.rules || []')
      .km-description.text-secondary-text The exact model name/deployment name used by the provider (case-sensitive)

  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md System name
    .full-width
      km-input(height='30px', placeholder='E.g. GPT-4O-MINI', v-model='system_name', ref='system_nameRef', :rules='config?.system_name?.rules || []')
      .km-description.text-secondary-text System name serves as a unique ID (auto-generated)

  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Display name
    .full-width
      km-input(
        height='30px',
        placeholder='E.g. GPT 4o mini',
        v-model='display_name',
        ref='display_nameRef',
        :rules='config?.display_name?.rules || []'
      )
      .km-description.text-secondary-text How the model name is displayed in the UI

  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Type
    .full-width
      km-select(
        height='auto',
        minHeight='30px',
        placeholder='Type',
        v-model='newRow.type',
        ref='typeRef',
        :options='categoryOptions',
        :rules='config?.type?.rules || []',
        emit-value,
        map-options
      )
      .km-description.text-secondary-text {{ typeDescription }}
</template>

<script>
import { ref, reactive } from 'vue'
import { useChroma, toUpperCaseWithUnderscores } from '@shared'
import { categoryOptions } from '../../config/model/model.js'

export default {
  props: {
    showNewDialog: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['cancel'],
  setup() {
    const { config, create, requiredFields } = useChroma('model')

    return {
      config,
      create,
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
    }
  },
  computed: {
    provider() {
      return this.$store.getters.provider
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
  },
  beforeUnmount() {
    this.isMounted = false
  },
  methods: {
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
      const validStates = this.requiredFields.map((field) => this.$refs[`${field}Ref`]?.validate())
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

      await this.create(JSON.stringify(payload))
      this.$emit('cancel')
    },
  },
}
</script>

<style lang="stylus" scoped>
.km-input:not(.q-field--readonly) .q-field__control::before
  background: #fff !important;
</style>
