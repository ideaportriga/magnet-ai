<template lang="pug">
div
  km-section(
    title='Detect question language',
    subTitle='Can be used independently for monitoring purposes and is required for multi-lingual search. Makes one extra call to LLM.'
  )
    q-toggle.q-mb-lg(v-model='isDetectLanguage', dense)
      km-notification-text(
        v-if='isMultiLingualRAG',
        notification='When "Detect question language" is disabled, "Enable multi-lingual Retrieval" will also be disabled',
        tooltip
      )
    template(v-if='isDetectLanguage')
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Detection Prompt Template
      km-select(height='30px', placeholder='Detect Q&A Language', :options='prompts', v-model='detectLanguagePromptTemplate', hasDropdownSearch)
      .row.q-mt-sm
        .col-auto
          km-btn(
            flat,
            simple,
            :label='detectLanguagePromptTemplate ? "Open Prompt Template" : "Open Prompt Templates Library"',
            iconSize='16px',
            icon='fas fa-comment-dots',
            @click='detectLanguagePromptTemplate ? navigate(`prompt-templates/${detectLanguagePromptTemplateId}`) : navigate("prompt-templates")'
          )

  q-separator.q-my-lg
  km-section(
    title='Enable multi-lingual Retrieval',
    subTitle='Optimizes Retrieval Tool for questions in other languages than knowledge source language. Makes one extra call to LLM.'
  )
    q-toggle.q-mb-lg(v-model='isMultiLingualRAG', dense, :disable='!isDetectLanguage')
      km-notification-text(v-if='!isDetectLanguage', notification='Language detection must be on to enable multi-lingual Retrieval', tooltip)
    template(v-if='isMultiLingualRAG')
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 RAG Tool source language
      km-select(height='30px', placeholder='RAG Tool source language', :options='languages', v-model='RetrievalToolSourceLangualge')
      q-separator.q-my-lg
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Translation Prompt Template
      km-select(height='30px', placeholder='Translation Prompt Template', :options='prompts', v-model='translatePromptTemplate', hasDropdownSearch)
      .row.q-mt-sm
        .col-auto
          km-btn(
            flat,
            simple,
            :label='translatePromptTemplate ? "Open Prompt Template" : "Open Prompt Templates Library"',
            iconSize='16px',
            icon='fas fa-comment-dots',
            @click='translatePromptTemplate ? navigate(`prompt-templates/${TranslatePromptTemplateId}`) : navigate("prompt-templates")'
          )
</template>

<script>
export default {
  emits: ['openTest'],
  computed: {
    languages() {
      return ['English', 'Finnish', 'French', 'German', 'Latvian', 'Spanish', 'Swedish'].map((el) => ({ value: el, label: el }))
    },
    isDetectLanguage: {
      get() {
        return this.$store.getters.retrievalVariant?.language?.detect_question_language?.enabled || false
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'language.detect_question_language.enabled', value })
      },
    },
    isMultiLingualRAG: {
      get() {
        return this.$store.getters.retrievalVariant?.language?.multilanguage?.enabled || false
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'language.multilanguage.enabled', value })
      },
    },
    promptsWithId() {
      return (this.$store.getters.prompts ?? []).map((item) => ({ label: item.name, value: item.system_name, id: item.id }))
    },
    detectLanguagePromptTemplateId() {
      return this.promptsWithId.find((el) => el.value == this.$store.getters.retrievalVariant?.language?.detect_question_language?.prompt_template)?.id
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
      return this.$store.getters.retrievalVariant?.language?.detect_question_language?.prompt_template || ''
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
      return this.$store.getters.retrievalVariant?.language?.multilanguage?.prompt_template_translation || ''
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
      return this.promptsWithId.find((el) => el.value == this.$store.getters.retrievalVariant?.language?.multilanguage?.prompt_template_translation)?.id
    },
    RetrievalToolSourceLangualge: {
      get() {
        return this.$store.getters.retrievalVariant?.language?.multilanguage?.source_language || ''
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
