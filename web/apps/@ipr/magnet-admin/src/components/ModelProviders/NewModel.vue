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
  km-stepper.full-width(v-if='steps?.length > 1', :steps='steps', :stepper='stepper')
  
  template(v-if='stepper == 0')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Provider model name
      .full-width
        km-input(
          height='30px',
          placeholder='E.g. gpt-4o-mini',
          v-model='model',
          ref='modelRef',
          :rules='config?.model?.rules || []'
        )
        .km-description.text-secondary-text Name used by the provider to identify the model
    
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md System name
      .full-width
        km-input(
          height='30px',
          placeholder='E.g. GPT-4O-MINI',
          v-model='system_name',
          ref='system_nameRef',
          :rules='config?.system_name?.rules || []'
        )
        .km-description.text-secondary-text System name serves as a unique ID

    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Display name
      .full-width
        km-input(
          height='30px',
          placeholder='E.g. GPT 4o mini',
          v-model='newRow.display_name',
          ref='display_nameRef',
          :rules='config?.display_name?.rules || []'
        )
        .km-description.text-secondary-text How the model name is displayed

    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Category
      .full-width
        km-select(
          height='auto',
          minHeight='30px',
          placeholder='Category',
          v-model='newRow.type',
          ref='typeRef',
          :options='categoryOptions',
          :rules='config?.type?.rules || []',
          emit-value,
          map-options
        )

  template(v-if='stepper == 1')
    div(v-if='newRow.type === "prompts"')
      .km-title.q-mb-md Structured outputs
      .row.items-center
        q-toggle(v-model='newRow.json_mode')
        .km-field.text-secondary-text Supports JSON mode
      .row.items-center
        q-toggle(v-model='newRow.json_schema')
        .km-field.text-secondary-text Supports JSON schema

      q-separator.q-my-md
      .km-title.q-mb-md Tool calling
      .row.items-center
        q-toggle(v-model='newRow.tool_calling')
        .km-field.text-secondary-text Tool calling
      
      q-separator.q-my-md
      .km-title.q-mb-md Reasoning
      .row.items-center
        q-toggle(v-model='newRow.reasoning')
        .km-field.text-secondary-text Reasoning
</template>

<script>
import { ref, reactive } from 'vue'
import { useChroma, toUpperCaseWithUnderscores } from '@shared'

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
      stepper: ref(0),
      autoChangeCode: ref(true),
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
      }),
    }
  },
  data() {
    return {
      categoryOptions: [
        { label: 'Chat Completion', value: 'prompts' },
        { label: 'Vector Embedding', value: 'embeddings' },
        { label: 'Re-ranking', value: 're-ranking' },
      ],
      isMounted: false,
    }
  },
  computed: {
    provider() {
      return this.$store.getters.provider
    },
    steps() {
      if (this.newRow.type === 'prompts') {
        return [
          { step: 0, description: 'Settings', icon: 'pen' },
          { step: 1, description: 'Capabilities', icon: 'circle' },
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
    popupTitle() {
      if (this.newRow.type === 're-ranking') {
        return 'New Re-ranking Model'
      }
      if (this.newRow.type === 'embeddings') {
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
        if (this.autoChangeCode && this.isMounted && this.provider?.system_name) {
          this.newRow.system_name = toUpperCaseWithUnderscores(this.provider.system_name + '_' + val)
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