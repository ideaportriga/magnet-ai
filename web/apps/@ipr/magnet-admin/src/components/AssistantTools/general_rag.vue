<template lang="pug">
div
  km-section(title='Type', subTitle='Operation type')
    .km-field.text-secondary-text.q-pb-md.q-pl-8 Operation type
      km-select(
        height='30px',
        placeholder='Type',
        :options='typeOptions',
        v-model='type',
        hasDropdownSearch,
        option-value='value',
        option-label='label',
        map-options,
        disabled
      )
  q-separator.q-my-lg
  km-section(title='RAG Tools')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 RAG Tools
      km-select(
        height='auto',
        minHeight='36px',
        placeholder='Select RAG',
        :options='ragItems',
        v-model='rag',
        hasDropdownSearch,
        option-value='system_name',
        option-label='name',
        emit-value,
        map-options,
        disabled
      )

  q-separator.q-my-lg
  km-section(title='Descriptions for LLM', subTitle='Descriptions by which the LLM will choose this Assistant Tool')
    .km-field.text-secondary-text.q-pb-md.q-pl-8 Name
      km-input(v-model='nameForLLM', placeholder='Max chunk size')
      .km-description.text-secondary-text Tool name for the LLM

    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Description
      km-input(
        ref='input',
        rows='10',
        placeholder='Type your text here',
        border-radius='8px',
        height='36px',
        type='textarea',
        v-model='descriptionForLLM'
      )
      .km-description.text-secondary-textTool Description for the LLM
</template>

<script>
import { useChroma } from '@shared'

export default {
  emits: ['openTest'],

  setup() {
    const { items: ragItems } = useChroma('rag_tools')
    return {
      ragItems,
    }
  },
  computed: {
    rag: {
      get() {
        return this.$store.getters.assistant_tool?.rag?.rag_tool || ''
      },
      set(value) {
        this.$store.dispatch('updateRetrievalProperty', { path: 'rag.rag_tool', value })
      },
    },
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
        return this.$store.getters.assistant_tool?.type || ''
      },
      set(value) {
        this.$store.dispatch('updateNestedAssistantToolProperty', { path: 'type', value })
      },
    },
    descriptionForLLM: {
      get() {
        return this.$store.getters.assistant_tool?.definition?.function?.description || ''
      },
      set(value) {
        this.$store.dispatch('updateNestedAssistantToolProperty', { path: 'definition.function.description', value })
      },
    },
    nameForLLM: {
      get() {
        return this.$store.getters.assistant_tool?.definition?.function?.name || ''
      },
      set(value) {
        this.$store.dispatch('updateNestedAssistantToolProperty', { path: 'definition.function.name', value })
      },
    },
    languages() {
      return ['English', 'Finnish', 'French', 'German', 'Latvian', 'Spanish', 'Swedish'].map((el) => ({ value: el, label: el }))
    },
    isDetectLanguage: {
      get() {
        return this.$store.getters.assistant_tool?.language?.detect_question_language?.enabled || false
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'language.detect_question_language.enabled', value })
      },
    },
    isMultiLingualRAG: {
      get() {
        return this.$store.getters.assistant_tool?.language?.multilanguage?.enabled || false
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'language.multilanguage.enabled', value })
      },
    },
    promptsWithId() {
      return (this.$store.getters.prompts ?? []).map((item) => ({ label: item.name, value: item.system_name, id: item.id }))
    },
    detectLanguagePromptTemplateId() {
      return this.promptsWithId.find((el) => el.value == this.$store.getters.assistant_tool?.language?.detect_question_language?.prompt_template)?.id
    },
    prompts() {
      return (this.$store.getters.prompts ?? [])
        .map((item) => ({ label: item.name, value: item.id, system_name: item.system_name, category: item?.category }))
        .filter((el) => el.category === 'rag')
    },
    propmt_name() {
      return (this.$store.getters.prompts ?? []).find((el) => el.system_name === this.prompt_template)?.name
    },
    prompt_template() {
      return this.$store.getters.assistant_tool?.language?.detect_question_language?.prompt_template || ''
    },
    detectLanguagePromptTemplate: {
      get() {
        return this.propmt_name
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'language.detect_question_language.prompt_template', value: value.system_name })
      },
    },
    prompt_template_multilingual() {
      return this.$store.getters.assistant_tool?.language?.multilanguage?.prompt_template_translation || ''
    },
    propmt_name_multilingual() {
      return (this.$store.getters.prompts ?? []).find((el) => el.system_name === this.prompt_template_multilingual)?.name
    },
    translatePromptTemplate: {
      get() {
        return this.propmt_name_multilingual
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', {
          path: 'language.multilanguage.prompt_template_translation',
          value: value.system_name,
        })
      },
    },
    TranslatePromptTemplateId() {
      return this.promptsWithId.find((el) => el.value == this.$store.getters.assistant_tool?.language?.multilanguage?.prompt_template_translation)?.id
    },
    RetrievalToolSourceLangualge: {
      get() {
        return this.$store.getters.assistant_tool.language.multilanguage.source_language || ''
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'language.multilanguage.source_language', value: value.value })
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
