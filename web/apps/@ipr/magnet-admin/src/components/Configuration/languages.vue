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
    :title='m.ragTools_enableMultiLingualRag()',
    :subTitle='m.subtitle_optimizeRag()'
  )
    q-toggle.q-mb-lg.q-pl-8(v-model='isMultiLingualRAG', dense)
    template(v-if='isMultiLingualRAG')
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.ragTools_ragToolSourceLanguage() }}
        km-select(height='30px', :placeholder='m.ragTools_ragToolSourceLanguage()', :options='languages', v-model='ragToolSourceLangualge')
      q-separator.q-my-lg
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.ragTools_detectionPromptTemplate() }}
        km-select(
          height='30px',
          :placeholder='m.ragTools_detectQaLanguage()',
          :options='promptTemplates',
          v-model='detectLanguagePromptTemplate',
          hasDropdownSearch
        )
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
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.ragTools_translationPromptTemplate() }}
        km-select(
          height='30px',
          :placeholder='m.ragTools_translationPromptTemplate()',
          :options='promptTemplates',
          v-model='translatePromptTemplate',
          hasDropdownSearch
        )
        .row.q-mt-sm
          .col-auto
            km-btn(
              flat,
              simple,
              :label='translatePromptTemplate ? m.common_openPromptTemplate() : m.common_openPromptTemplatesLibrary()',
              iconSize='16px',
              icon='fas fa-comment-dots',
              @click='translatePromptTemplate ? navigate(`prompt-templates/${translatePromptTemplateId}`) : navigate("prompt-templates")'
            )
</template>

<script>
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'
export default {
  emits: ['openTest'],
  setup() {
    const queries = useEntityQueries()
    const { activeVariant, updateVariantField } = useVariantEntityDetail('rag_tools')
    const { data: promptTemplateListData } = queries.promptTemplates.useList()

    return {
      m,
      activeVariant,
      updateVariantField,
      promptTemplateListData,
    }
  },
  computed: {
    promptTemplateItems() {
      return this.promptTemplateListData?.items ?? []
    },
    languages() {
      return ['English', 'Finnish', 'French', 'German', 'Latvian', 'Russian', 'Spanish', 'Swedish', 'Uzbek'].map((el) => ({ value: el, label: el }))
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
      return (this.promptTemplateItems ?? []).map((item) => ({ label: item.name, value: item.system_name, id: item.id }))
    },
    detectLanguagePromptTemplateId() {
      return this.promptsWithId.find((el) => el.value == this.activeVariant?.language?.detect_question_language?.prompt_template)?.id
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
      return (this.promptTemplates ?? []).find((el) => el.system_name === this.prompt_template_multilingual)?.label
    },
    translatePromptTemplate: {
      get() {
        return this.propmt_name_multilingual
      },
      set(value) {
        this.updateVariantField('language.multilanguage.prompt_template_translation', value.system_name)
      },
    },
    translatePromptTemplateId() {
      return this.promptsWithId.find((el) => el.value == this.activeVariant?.language?.multilanguage?.prompt_template_translation)?.id
    },
    ragToolSourceLangualge: {
      get() {
        return this.activeVariant?.language.multilanguage.source_language || ''
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
