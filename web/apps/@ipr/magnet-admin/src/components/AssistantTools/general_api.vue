<template>
  <div>
    <km-section :title="m.common_settings()" :sub-title="m.subtitle_assistantToolParams()">
      <div class="km-field text-secondary-text pb-md pl-sm">
        Operation type
        <km-select v-model="type" height="30px" :placeholder="m.common_type()" :options="typeOptions" has-dropdown-search option-value="value" option-label="label" map-options disabled />
      </div>
      <div class="km-field text-secondary-text pb-xs pl-sm">
        API Provider
        <km-select v-model="provider" height="30px" :placeholder="m.label_apiProvider()" :options="[{ value: &quot;siebel_test&quot;, label: &quot;API Provider Siebel Test&quot; }]" has-dropdown-search option-value="value" option-label="label" map-options disabled />
      </div>
    </km-section>
    <km-separator class="my-lg" />
    <km-section :title="m.section_descriptionsForLlm()" :sub-title="m.subtitle_llmDescriptions()">
      <div class="km-field text-secondary-text pb-md pl-sm">
        Name
        <km-input v-model="nameForLLM" :placeholder="m.assistantTools_toolNameForLlm()" />
        <div class="km-description text-secondary-text">Tool name for the LLM</div>
      </div>
      <div class="km-field text-secondary-text pb-xs pl-sm">
        Description
        <km-input ref="input" v-model="descriptionForLLM" rows="10" :placeholder="m.placeholder_typeYourTextHere()" border-radius="8px" height="36px" type="textarea" />
        <div class="km-description text-secondary-textTool">Description for the LLM</div>
      </div>
    </km-section>
    <km-separator class="my-lg" />
    <km-section :title="m.section_requireConfirmation()" :sub-title="m.subtitle_requireConfirmation()">
      <div class="stack" data-gap="0">
        <div class="flex-1 mb-md">
          <km-chip tone="brand" class="km-small-chip" :label="m.common_upcomingFeature()" />
        </div>
        <div class="flex-1">
          <km-toggle :model-value="true" disable dense />
        </div>
      </div>
    </km-section>
  </div>
</template>

<script>
import { computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'
import { useEntityDetail } from '@/composables/useEntityDetail'

export default {
  emits: ['openTest'],
  setup() {
    const queries = useEntityQueries()
    const { draft, updateField } = useEntityDetail('assistant_tools')
    const { data: promptListData } = queries.promptTemplates.useList()
    const promptItems = computed(() => promptListData.value?.items ?? [])
    return {
      m,
      provider: 'siebel_test',
      draft,
      updateField,
      promptItems,
    }
  },
  computed: {
    typeOptions() {
      return [
        {
          value: 'api',
          label: 'API',
        },
        {
          value: 'rag',
          label: 'RAG',
        },
      ]
    },
    type: {
      get() {
        return this.draft?.type || ''
      },
      set(value) {
        this.updateField('type', value)
      },
    },
    descriptionForLLM: {
      get() {
        return this.draft?.definition?.function?.description || ''
      },
      set(value) {
        this.updateField('definition.function.description', value)
      },
    },
    nameForLLM: {
      get() {
        return this.draft?.definition?.function?.name || ''
      },
      set(value) {
        this.updateField('definition.function.name', value)
      },
    },

    languages() {
      return ['English', 'Finnish', 'French', 'German', 'Latvian', 'Spanish', 'Swedish'].map((el) => ({ value: el, label: el }))
    },
    isDetectLanguage: {
      get() {
        return this.draft?.language?.detect_question_language?.enabled || false
      },
      set(value) {
        this.updateField('language.detect_question_language.enabled', value)
      },
    },
    isMultiLingualRAG: {
      get() {
        return this.draft?.language?.multilanguage?.enabled || false
      },
      set(value) {
        this.updateField('language.multilanguage.enabled', value)
      },
    },
    promptsWithId() {
      return (this.promptItems ?? []).map((item) => ({ label: item.name, value: item.system_name, id: item.id }))
    },
    detectLanguagePromptTemplateId() {
      return this.promptsWithId.find((el) => el.value == this.draft?.language?.detect_question_language?.prompt_template)?.id
    },
    prompts() {
      return (this.promptItems ?? [])
        .map((item) => ({ label: item.name, value: item.id, system_name: item.system_name, category: item?.category }))
        .filter((el) => el.category === 'rag')
    },
    propmt_name() {
      return (this.promptItems ?? []).find((el) => el.system_name === this.prompt_template)?.name
    },
    prompt_template() {
      return this.draft?.language?.detect_question_language?.prompt_template || ''
    },
    detectLanguagePromptTemplate: {
      get() {
        return this.propmt_name
      },
      set(value) {
        this.updateField('language.detect_question_language.prompt_template', value.system_name)
      },
    },
    prompt_template_multilingual() {
      return this.draft?.language?.multilanguage?.prompt_template_translation || ''
    },
    propmt_name_multilingual() {
      return (this.promptItems ?? []).find((el) => el.system_name === this.prompt_template_multilingual)?.name
    },
    translatePromptTemplate: {
      get() {
        return this.propmt_name_multilingual
      },
      set(value) {
        this.updateField('language.multilanguage.prompt_template_translation', value.system_name)
      },
    },
    TranslatePromptTemplateId() {
      return this.promptsWithId.find((el) => el.value == this.draft?.language?.multilanguage?.prompt_template_translation)?.id
    },
    RetrievalToolSourceLangualge: {
      get() {
        return this.draft.language.multilanguage.source_language || ''
      },
      set(value) {
        this.updateField('language.multilanguage.source_language', value.value)
      },
    },
  },
  watch: {
    isDetectLanguage(newVal, oldVal) {
      if (!newVal && newVal !== oldVal) {
        this.isMultiLingualRAG = false
      }
    },
  },
  methods: {
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`/${path}`)
      }
    },
  },
}
</script>
