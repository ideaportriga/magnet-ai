<template lang="pug">
div
  km-section(title='LLM model', subTitle='Choose what model you will use for output generation.')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 LLM Model
    km-select(
      height='auto',
      minHeight='36px',
      placeholder='LLM Model',
      v-model='model',
      :options='modelOptions',
      optionLabel='display_name',
      emit-value,
      hasDropdownSearch
    )
      template(#option='{ itemProps, opt, selected, toggleOption }')
        q-item.ba-border(v-bind='itemProps', dense, @click='toggleOption(opt)')
          q-item-section
            q-item-label.km-label {{ opt.display_name }}
            .row.q-mt-xs(v-if='opt.provider_system_name')
              q-chip(color='primary-light', text-color='primary', size='sm', dense) {{ opt.provider_system_name }}
  q-separator.q-my-lg
  km-section(
    v-if='showTemperature || showTopP',
    title='Parameters',
    subTitle='Temperature controls randomness of output. Top p controls diversity and unpredictability of output. Reasoning effort controls how much effort reasoning models spend on the answer. Use default values if you are not certain about these parameters.'
  )
    km-slider-card.q-mb-lg(
      v-if='showTemperature',
      v-model='temperature',
      name='Temperature',
      :min='0',
      :max='2',
      :defaultValue='1',
      minLabel='Less random',
      maxLabel='More random',
      description='We generally recommend altering this or top p, but not both.',
      infoTooltip='Temperature controls randomness of output.'
    )

  km-section(v-if='showTopP')
    km-slider-card(
      v-model='topP',
      name='Top P',
      :min='0',
      :max='1',
      :defaultValue='1',
      minLabel='Less diverse',
      maxLabel='More diverse',
      description='We generally recommend altering this or top p, but not both.',
      infoTooltip='Top p controls diversity and unpredictability of output.'
    )
  km-section(v-if='showReasoningEffortSelector')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-md Reasoning Effort
    km-select(
      height='auto',
      minHeight='36px',
      placeholder='Select reasoning effort',
      v-model='reasoningEffort',
      :options='reasoningEffortOptions',
      optionLabel='label',
      optionValue='value',
      emit-value,
      map-options,
      clearable
    )
    .km-description.text-secondary-text.q-pt-xs.q-pl-8 Controls how much effort the reasoning model spends on the answer. Available values are configured per-model.
  q-separator.q-my-lg(v-if='showMaxTokens')
  km-section(v-if='showMaxTokens', title='Output limit', subTitle='Limits generated output length. Leave blank if not necessary')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Max tokens
      div(style='max-width: 200px')
        km-input(type='number', height='30px', placeholder='Max tokens', v-model='maxTokens')
      .km-description.text-secondary-text.q-pb-4 1 token = approx. 4 characters in English
  q-separator.q-my-lg
  km-section(
    title='Observability',
    subTitle='Control what data is logged for this prompt template. This affects traces and metrics collection.'
  )
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Logging Level
    km-select(
      height='auto',
      minHeight='36px',
      placeholder='Select logging level',
      v-model='observabilityLevel',
      :options='observabilityLevelOptions',
      optionLabel='label',
      optionValue='value',
      emit-value,
      map-options
    )
    .km-description.text-secondary-text.q-pt-xs.q-pl-8 {{ observabilityLevelDescription }}
</template>

<script>
import { isEqual } from 'lodash'
import { ref } from 'vue'
import { useChroma } from '@shared'

export default {
  props: ['prompt', 'selectedRow'],
  emits: ['setProp', 'save', 'cancel', 'remove', 'openTest'],

  setup() {
    const { publicItems, publicSelected, publicSelectedOptionsList } = useChroma('collections')

    return {
      publicItems,
      publicSelected,
      publicSelectedOptionsList,
      test: ref(true),
      iconPicker: ref(false),
      showError: ref(false),
      selectedEntity: ref(),
      promptInput: ref(null),
      llm: ref(true),
      semanticCache: ref(false),
      semanticCacheChoice: ref('faq'),
      isReRanking: ref(false),
      reRankingChoice: ref('cross'),
      reRankingCrossModel: ref(''),
      reRankingLlmModel: ref(''),
      cacheCollection: ref('Helpdesk Cache'),
      allowBypassCache: ref(false),
      collections: publicItems,
      observabilityLevelOptions: ref([
        { label: 'Full (input/output included)', value: 'full' },
        { label: 'Metadata only (tokens, cost, latency)', value: 'metadata-only' },
        { label: 'None (no logging)', value: 'none' },
      ]),
    }
  },
  computed: {
    observabilityLevel: {
      get() {
        return this.$store.getters.promptTemplateVariant?.observability_level || 'full'
      },
      set(value) {
        this.$store.commit('updateNestedPromptTemplateProperty', { path: 'observability_level', value })
      },
    },
    observabilityLevelDescription() {
      const descriptions = {
        'full': 'Logs everything including input messages and output responses. Best for debugging and analysis.',
        'metadata-only': 'Logs only metadata like token count, cost, and latency. Input/output content is not stored.',
        'none': 'Disables all logging for this prompt template. No traces or metrics will be recorded.',
      }
      return descriptions[this.observabilityLevel] || descriptions['full']
    },
    temperature: {
      get() {
        return this.$store.getters.promptTemplateVariant?.temperature
      },
      set(value) {
        this.$store.commit('updateNestedPromptTemplateProperty', { path: 'temperature', value })
      },
    },
    maxTokens: {
      get() {
        return this.$store.getters.promptTemplateVariant?.maxTokens || null
      },
      set(value) {
        const intValue = parseInt(value, 10)

        if (!isNaN(intValue)) {
          this.$store.commit('updateNestedPromptTemplateProperty', { path: 'maxTokens', value: intValue })
        }
      },
    },

    topP: {
      get() {
        return this.$store.getters.promptTemplateVariant?.topP
      },
      set(value) {
        this.$store.commit('updateNestedPromptTemplateProperty', { path: 'topP', value })
      },
    },
    reasoningEffort: {
      get() {
        return this.$store.getters.promptTemplateVariant?.reasoning_effort || null
      },
      set(value) {
        this.$store.commit('updateNestedPromptTemplateProperty', { path: 'reasoning_effort', value: value || null })
      },
    },
    selectedModel() {
      const sysName = this.$store.getters.promptTemplateVariant?.system_name_for_model
      if (!sysName) return null
      return (this.$store.getters['chroma/model'].items || []).find((m) => m?.system_name === sysName) || null
    },
    reasoningEffortOptions() {
      const opts = this.selectedModel?.reasoning_effort_options || []
      return opts.map((v) => ({ label: v, value: v }))
    },
    showReasoningEffortSelector() {
      return !!this.selectedModel?.reasoning && this.reasoningEffortOptions.length > 0
    },
    showTemperature() {
      return this.selectedModel?.supports_temperature !== false
    },
    showTopP() {
      return this.selectedModel?.supports_top_p !== false
    },
    showMaxTokens() {
      return this.selectedModel?.supports_max_tokens !== false
    },
    model: {
      get() {
        return this.model_name || ''
      },
      set(value) {
        this.$store.commit('updateNestedPromptTemplateProperty', { path: 'system_name_for_model', value: value.system_name })
        // TODO: remove this when the backend is updated to use system_name_for_model. This is for supporting the old model field
        this.$store.commit('updateNestedPromptTemplateProperty', { path: 'model', value: value.model })
      },
    },
    model_name() {
      if (this.$store.getters.promptTemplateVariant?.system_name_for_model) {
        return (this.modelOptions ?? []).find((el) => el?.system_name === this.$store.getters.promptTemplateVariant?.system_name_for_model)
          ?.display_name
      }
      // TODO: remove this when the backend is updated to use system_name_for_model. This is for supporting the old model field
      return (this.modelOptions ?? []).find((el) => el.model === this.$store.getters.promptTemplateVariant?.model)?.display_name
    },
    modelOptions() {
      return (this.$store.getters['chroma/model'].items || [])
        .filter((el) => el.type === 'prompts')
        .sort((a, b) => a.display_name.localeCompare(b.display_name))
    },

    hasChanges() {
      if (this.selectedRow?.id !== undefined) return !isEqual(this.prompt, this.selectedRow)
      else return true
    },
    hasError() {
      return !(this.prompt.name && this.prompt.text && this.prompt.description)
    },
    isNew() {
      return this.prompt && this.prompt.id === undefined
    },
    canSave() {
      return !!this.prompt.text && !!this.prompt.description && !!this.prompt.name
    },
  },
  watch: {
    selectedModel() {
      const variant = this.$store.getters.promptTemplateVariant
      const current = variant?.reasoning_effort
      if (current) {
        const allowed = this.selectedModel?.reasoning_effort_options || []
        if (!allowed.includes(current)) {
          this.$store.commit('updateNestedPromptTemplateProperty', { path: 'reasoning_effort', value: null })
        }
      }
      if (this.selectedModel?.supports_temperature === false && variant?.temperature != null) {
        this.$store.commit('updateNestedPromptTemplateProperty', { path: 'temperature', value: null })
      }
      if (this.selectedModel?.supports_top_p === false && variant?.topP != null) {
        this.$store.commit('updateNestedPromptTemplateProperty', { path: 'topP', value: null })
      }
      if (this.selectedModel?.supports_max_tokens === false && variant?.maxTokens != null) {
        this.$store.commit('updateNestedPromptTemplateProperty', { path: 'maxTokens', value: null })
      }
    },
  },
  created() {},
  methods: {
    setProp(name, val) {
      this.$emit('setProp', { name, val })
    },
    save() {
      if (this.hasError) {
        this.showError = true
        return
      }
      this.showError = false
      this.$emit('save')
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`/${path}`)
      }
    },
  },
}
</script>
