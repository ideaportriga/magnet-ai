<template lang="pug">
div
  km-section(:title='m.common_type()', :subTitle='m.subtitle_operationType()')
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
  km-section(:title='m.entity_ragtools()')
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
  km-section(:title='m.section_descriptionsForLlm()', :subTitle='m.subtitle_llmDescriptions()')
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
import { useEntityQueries } from '@/queries/entities'
import { useCatalogOptions } from '@/queries/useCatalogOptions'
import { m } from '@/paraglide/messages'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { computed } from 'vue'

export default {
  emits: ['openTest'],

  setup() {
    const queries = useEntityQueries()
    const { draft, updateField } = useEntityDetail('assistant_tools')
    const { options: ragItems } = useCatalogOptions('rag_tools')
    const { data: promptListData } = queries.promptTemplates.useList()
    const promptItems = computed(() => promptListData.value?.items ?? [])
    return {
      m,
      ragItems,
      draft,
      updateField,
      promptItems,
    }
  },
  computed: {
    rag: {
      get() {
        return this.draft?.rag?.rag_tool || ''
      },
      set(value) {
        this.updateField('rag.rag_tool', value)
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
