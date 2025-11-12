<template lang="pug">
div
  //- km-section(
  //-   title='Detect question language',
  //-   subTitle='Can be used independently for monitoring purposes and is required for multi-lingual RAG. Makes one extra call to LLM.'
  //- )
    //- q-toggle.q-mb-lg(v-model='isDetectLanguage', dense)
    //-   km-notification-text(
    //-     v-if='isMultiLingualRAG',
    //-     notification='When "Detect question language" is disabled, "Enable multi-lingual RAG" will also be disabled',
    //-     tooltip
    //-   )


  km-section(
    title='Enable multi-lingual RAG',
    subTitle='Optimizes RAG for translation when users ask in other languages than knowledge source language. Makes 3 extra calls to LLM.'
  )
    q-toggle.q-mb-lg.q-pl-8(v-model='isMultiLingualRAG', dense)
    template(v-if='isMultiLingualRAG')
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 RAG Tool source language
        km-select(height='30px', placeholder='RAG Tool source language', :options='languages', v-model='ragToolSourceLangualge')
      q-separator.q-my-lg
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Detection Prompt Template
        km-select(
          height='30px',
          placeholder='Detect Q&A Language',
          :options='promptTemplates',
          v-model='detectLanguagePromptTemplate',
          hasDropdownSearch
        )
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
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Translation Prompt Template
        km-select(
          height='30px',
          placeholder='Translation Prompt Template',
          :options='promptTemplates',
          v-model='translatePromptTemplate',
          hasDropdownSearch
        )
        .row.q-mt-sm
          .col-auto
            km-btn(
              flat,
              simple,
              :label='translatePromptTemplate ? "Open Prompt Template" : "Open Prompt Templates Library"',
              iconSize='16px',
              icon='fas fa-comment-dots',
              @click='translatePromptTemplate ? navigate(`prompt-templates/${translatePromptTemplateId}`) : navigate("prompt-templates")'
            )
</template>

<script>
import { useChroma } from '@shared'
export default {
  emits: ['openTest'],
  setup() {
    const { items: promptTemplateItems } = useChroma('promptTemplates')

    return {
      promptTemplateItems,
    }
  },
  computed: {
    languages() {
      return ['English', 'Finnish', 'French', 'German', 'Latvian', 'Russian', 'Spanish', 'Swedish', 'Uzbek'].map((el) => ({ value: el, label: el }))
    },
    isMultiLingualRAG: {
      get() {
        return this.$store.getters.ragVariant?.language?.multilanguage?.enabled || false
      },
      set(value) {
        this.$store.dispatch('updateNestedRagProperty', { path: 'language.multilanguage.enabled', value })
      },
    },
    promptsWithId() {
      return (this.promptTemplateItems ?? []).map((item) => ({ label: item.name, value: item.system_name, id: item.id }))
    },
    detectLanguagePromptTemplateId() {
      return this.promptsWithId.find((el) => el.value == this.$store.getters.ragVariant?.language?.detect_question_language?.prompt_template)?.id
    },
    promptTemplates() {
      return (this.promptTemplateItems ?? [])
        .map((item) => ({
          label: item.name,
          value: item.id,
          system_name: item.system_name,
          category: item?.category,
        }))
        .filter((el) => el.category === 'rag')
    },
    propmt_name() {
      return (this.promptTemplates ?? []).find((el) => el.system_name === this.prompt_template)?.label
    },
    prompt_template() {
      return this.$store.getters.ragVariant?.language?.detect_question_language?.prompt_template || ''
    },
    detectLanguagePromptTemplate: {
      get() {
        return this.propmt_name
      },
      set(value) {
        this.$store.dispatch('updateNestedRagProperty', { path: 'language.detect_question_language.prompt_template', value: value.system_name })
      },
    },
    prompt_template_multilingual() {
      return this.$store.getters.ragVariant?.language?.multilanguage?.prompt_template_translation || ''
    },
    propmt_name_multilingual() {
      return (this.promptTemplates ?? []).find((el) => el.system_name === this.prompt_template_multilingual)?.label
    },
    translatePromptTemplate: {
      get() {
        return this.propmt_name_multilingual
      },
      set(value) {
        this.$store.dispatch('updateNestedRagProperty', { path: 'language.multilanguage.prompt_template_translation', value: value.system_name })
      },
    },
    translatePromptTemplateId() {
      return this.promptsWithId.find((el) => el.value == this.$store.getters.ragVariant?.language?.multilanguage?.prompt_template_translation)?.id
    },
    ragToolSourceLangualge: {
      get() {
        return this.$store.getters.ragVariant?.language.multilanguage.source_language || ''
      },
      set(value) {
        this.$store.dispatch('updateNestedRagProperty', { path: 'language.multilanguage.source_language', value: value.value })
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
