<template lang="pug">
div
  km-section(
    :title='m.retrieval_detectQuestionLanguage()',
    :subTitle='m.subtitle_detectLanguageRetrieval()'
  )
    q-toggle.q-mb-lg(v-model='isDetectLanguage', dense)
      km-notification-text(
        v-if='isMultiLingualRAG',
        :notification='m.retrieval_detectLanguageDisableWarning()',
        tooltip
      )
    template(v-if='isDetectLanguage')
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.retrieval_detectionPromptTemplate() }}
      km-select(height='30px', :placeholder='m.retrieval_detectQaLanguage()', :options='prompts', v-model='detectLanguagePromptTemplate', hasDropdownSearch)
      .row.q-mt-sm
        .col-auto
          km-btn(
            flat,
            simple,
            :label='detectLanguagePromptTemplate ? m.common_openPromptTemplate() : m.common_openPromptTemplatesLibrary()',
            iconSize='16px',
            icon='fas fa-comment-dots',
            @click='detectLanguagePromptTemplate ? navigate(`prompt-templates/${detectLanguagePromptTemplateId}`) : navigate("prompt-templates")'
          )

  q-separator.q-my-lg
  km-section(
    :title='m.retrieval_enableMultiLingualRetrieval()',
    :subTitle='m.subtitle_optimizeRetrieval()'
  )
    q-toggle.q-mb-lg(v-model='isMultiLingualRAG', dense, :disable='!isDetectLanguage')
      km-notification-text(v-if='!isDetectLanguage', :notification='m.retrieval_detectLanguageDisableNote()', tooltip)
    template(v-if='isMultiLingualRAG')
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.retrieval_ragToolSourceLanguage() }}
      km-select(height='30px', :placeholder='m.retrieval_ragToolSourceLanguage()', :options='languages', v-model='RetrievalToolSourceLangualge')
      q-separator.q-my-lg
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.retrieval_translationPromptTemplate() }}
      km-select(height='30px', :placeholder='m.retrieval_translationPromptTemplate()', :options='prompts', v-model='translatePromptTemplate', hasDropdownSearch)
      .row.q-mt-sm
        .col-auto
          km-btn(
            flat,
            simple,
            :label='translatePromptTemplate ? m.common_openPromptTemplate() : m.common_openPromptTemplatesLibrary()',
            iconSize='16px',
            icon='fas fa-comment-dots',
            @click='translatePromptTemplate ? navigate(`prompt-templates/${TranslatePromptTemplateId}`) : navigate("prompt-templates")'
          )
</template>

<script>
import { m } from '@/paraglide/messages'
import { computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'

export default {
  emits: ['openTest'],
  setup() {
    const queries = useEntityQueries()
    const { activeVariant, updateVariantField } = useVariantEntityDetail('retrieval')
    const { data: promptListData } = queries.promptTemplates.useList()
    const promptItems = computed(() => promptListData.value?.items ?? [])
    return { m, activeVariant, updateVariantField, promptItems }
  },
  computed: {
    languages() {
      return ['English', 'Finnish', 'French', 'German', 'Latvian', 'Spanish', 'Swedish'].map((el) => ({ value: el, label: el }))
    },
    isDetectLanguage: {
      get() {
        return this.activeVariant?.language?.detect_question_language?.enabled || false
      },
      set(value) {
        this.updateVariantField('language.detect_question_language.enabled', value)
      },
    },
    isMultiLingualRAG: {
      get() {
        return this.activeVariant?.language?.multilanguage?.enabled || false
      },
      set(value) {
        this.updateVariantField('language.multilanguage.enabled', value)
      },
    },
    promptsWithId() {
      return (this.promptItems ?? []).map((item) => ({ label: item.name, value: item.system_name, id: item.id }))
    },
    detectLanguagePromptTemplateId() {
      return this.promptsWithId.find((el) => el.value == this.activeVariant?.language?.detect_question_language?.prompt_template)
        ?.id
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
      return this.activeVariant?.language?.detect_question_language?.prompt_template || ''
    },
    detectLanguagePromptTemplate: {
      get() {
        return this.propmt_name
      },
      set(value) {
        this.updateVariantField('language.detect_question_language.prompt_template', value.system_name)
      },
    },
    prompt_template_multilingual() {
      return this.activeVariant?.language?.multilanguage?.prompt_template_translation || ''
    },
    propmt_name_multilingual() {
      return (this.promptItems ?? []).find((el) => el.system_name === this.prompt_template_multilingual)?.name
    },
    translatePromptTemplate: {
      get() {
        return this.propmt_name_multilingual
      },
      set(value) {
        this.updateVariantField('language.multilanguage.prompt_template_translation', value.system_name)
      },
    },
    TranslatePromptTemplateId() {
      return this.promptsWithId.find((el) => el.value == this.activeVariant?.language?.multilanguage?.prompt_template_translation)
        ?.id
    },
    RetrievalToolSourceLangualge: {
      get() {
        return this.activeVariant?.language?.multilanguage?.source_language || ''
      },
      set(value) {
        this.updateVariantField('language.multilanguage.source_language', value.value)
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
