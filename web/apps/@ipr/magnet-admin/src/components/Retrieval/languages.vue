<template>
  <div>
    <km-section :title="m.retrieval_detectQuestionLanguage()" :sub-title="m.subtitle_detectLanguageRetrieval()">
      <km-toggle v-model="isDetectLanguage" class="mb-lg" dense>
        <km-notification-text v-if="isMultiLingualRAG" :notification="m.retrieval_detectLanguageDisableWarning()" tooltip />
      </km-toggle>
      <template v-if="isDetectLanguage">
        <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.retrieval_detectionPromptTemplate() }}</div>
        <km-select v-model="detectLanguagePromptTemplate" height="30px" :placeholder="m.retrieval_detectQaLanguage()" :options="prompts" has-dropdown-search />
        <div class="cluster mt-sm">
          <div class="flex-none">
            <km-btn flat simple :label="detectLanguagePromptTemplate ? m.common_openPromptTemplate() : m.common_openPromptTemplatesLibrary()" icon-size="16px" icon="chat" @click="detectLanguagePromptTemplate ? navigate(`prompt-templates/${detectLanguagePromptTemplateId}`) : navigate(&quot;prompt-templates&quot;)" />
          </div>
        </div>
      </template>
    </km-section>
    <km-separator class="my-lg" />
    <km-section :title="m.retrieval_enableMultiLingualRetrieval()" :sub-title="m.subtitle_optimizeRetrieval()">
      <km-toggle v-model="isMultiLingualRAG" class="mb-lg" dense :disable="!isDetectLanguage">
        <km-notification-text v-if="!isDetectLanguage" :notification="m.retrieval_detectLanguageDisableNote()" tooltip />
      </km-toggle>
      <template v-if="isMultiLingualRAG">
        <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.retrieval_ragToolSourceLanguage() }}</div>
        <km-select v-model="RetrievalToolSourceLangualge" height="30px" :placeholder="m.retrieval_ragToolSourceLanguage()" :options="languages" />
        <km-separator class="my-lg" />
        <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.retrieval_translationPromptTemplate() }}</div>
        <km-select v-model="translatePromptTemplate" height="30px" :placeholder="m.retrieval_translationPromptTemplate()" :options="prompts" has-dropdown-search />
        <div class="cluster mt-sm">
          <div class="flex-none">
            <km-btn flat simple :label="translatePromptTemplate ? m.common_openPromptTemplate() : m.common_openPromptTemplatesLibrary()" icon-size="16px" icon="chat" @click="translatePromptTemplate ? navigate(`prompt-templates/${TranslatePromptTemplateId}`) : navigate(&quot;prompt-templates&quot;)" />
          </div>
        </div>
      </template>
    </km-section>
  </div>
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
