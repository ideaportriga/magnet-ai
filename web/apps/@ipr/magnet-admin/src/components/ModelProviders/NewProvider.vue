<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  title='New Model Provider',
  confirmButtonLabel='Save',
  cancelButtonLabel='Cancel',
  notification='You will be able to add security values and secrets later in Model Provider settings.',
  @confirm='createModelProvider',
  @cancel='$emit("cancel")'
)
  .column.q-gap-16
    .col
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Name
      .full-width
        km-input(data-test='name-input', height='30px', v-model='name', ref='nameRef', :rules='[required()]', placeholder='E.g. My OpenAI Provider')
      .km-description.text-secondary-text.q-pb-4.q-pl-8 Display name for this provider

    .col
      .km-field.text-secondary-text.q-pl-8 System name
      .full-width
        km-input(data-test='system-name-input', height='30px', v-model='system_name', ref='system_nameRef', :rules='[required()]', placeholder='E.g. MY_OPENAI_PROVIDER')
      .km-description.text-secondary-text.q-pb-4.q-pl-8 System name serves as a unique record ID (auto-generated from name)

    .col
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 API Type
      .full-width
        km-select(
          data-test='select-type',
          height='auto',
          minHeight='36px',
          placeholder='Select API Type',
          :options='typeOptions',
          v-model='newRow.type',
          ref='typeRef',
          :rules='[required()]',
          emit-value,
          mapOptions
        )
      .km-description.text-secondary-text.q-pb-4.q-pl-8 The type of API this provider uses

    .col
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Endpoint
        span.text-secondary-text.q-ml-4 (optional for OpenAI)
      .full-width
        km-input(
          data-test='endpoint-input',
          height='30px',
          v-model='newRow.endpoint',
          placeholder='https://api.example.com',
          :rules='[validateEndpoint]'
        )
      .km-description.text-secondary-text.q-pb-4.q-pl-8 {{ endpointHint }}
</template>

<script>
import { ref, reactive, computed } from 'vue'
import { useChroma, required, toUpperCaseWithUnderscores } from '@shared'
import { useRouter } from 'vue-router'

export default {
  props: {
    showNewDialog: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['cancel'],
  setup() {
    const { create, ...useCollection } = useChroma('provider')
    const router = useRouter()

    const typeOptions = [
      { label: 'OpenAI', value: 'openai' },
      { label: 'Azure OpenAI', value: 'azure_open_ai' },
      { label: 'Azure AI', value: 'azure_ai' },
      { label: 'Groq', value: 'groq' },
      { label: 'OCI', value: 'oci' },
      { label: 'OCI Llama', value: 'oci_llama' },
    ]

    // Validate endpoint URL format
    const validateEndpoint = (val) => {
      if (!val) return true // Empty is OK (optional for some providers)
      // Check if it's a valid URL
      try {
        const url = new URL(val)
        if (!['http:', 'https:'].includes(url.protocol)) {
          return 'Endpoint must use http:// or https://'
        }
        // Check for trailing slash warning
        if (val.endsWith('/')) {
          return 'Endpoint should not have a trailing slash'
        }
        return true
      } catch {
        return 'Please enter a valid URL (e.g., https://api.example.com)'
      }
    }

    return {
      create,
      useCollection,
      router,
      required,
      validateEndpoint,
      newRow: reactive({
        name: '',
        system_name: '',
        type: '',
        category: 'llm', // Set category for Model Providers
        endpoint: '',
        connection_config: {},
        secrets_encrypted: {},
        metadata_info: {},
      }),
      autoChangeCode: ref(true),
      isMounted: ref(false),
      typeOptions,
    }
  },
  computed: {
    name: {
      get() {
        return this.newRow?.name || ''
      },
      set(val) {
        this.newRow.name = val
        if (this.autoChangeCode && this.isMounted) this.newRow.system_name = toUpperCaseWithUnderscores(val)
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
    endpointHint() {
      const type = this.newRow?.type
      const hints = {
        openai: 'Leave empty to use official OpenAI API. Only specify for OpenAI-compatible APIs.',
        azure_open_ai: 'Required. Your Azure OpenAI resource URL (e.g., https://your-resource.openai.azure.com)',
        azure_ai: 'Required. Your Azure AI endpoint URL.',
        groq: 'Leave empty to use default Groq API endpoint.',
        oci: 'Required. Your OCI endpoint URL.',
        oci_llama: 'Required. Your OCI Llama endpoint URL.',
      }
      return hints[type] || 'Provider API endpoint URL. Warning: changing endpoint later will clear all secrets.'
    },
  },
  mounted() {
    this.isMounted = true
  },
  beforeUnmount() {
    this.isMounted = false
    this.$emit('cancel')
  },
  methods: {
    validateFields() {
      const validStates = [this.$refs.nameRef?.validate(), this.$refs.system_nameRef?.validate(), this.$refs.typeRef?.validate()]
      return !validStates.includes(false)
    },
    async createModelProvider() {
      if (!this.validateFields()) return

      const result = await this.create(JSON.stringify(this.newRow))

      if (!result?.id) {
        return
      }

      await this.useCollection.selectRecord(result.id)
      this.$router.push(`/model-providers/${result.id}`)
    },
  },
}
</script>
