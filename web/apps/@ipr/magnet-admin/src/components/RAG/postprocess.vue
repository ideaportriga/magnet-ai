<template>
  <div>
    <km-section :title="m.ragTools_enablePostProcessing()" :sub-title="m.subtitle_collectRagData()">
      <km-toggle v-model="postProcessEnabled" dense />
    </km-section>
    <template v-if="postProcessEnabled"> 
      <km-separator class="my-lg" />
      <km-section :title="m.agents_postProcessingPromptTemplate()" :sub-title="m.subtitle_selectPostProcessing()">
        <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_promptTemplate() }}</div>
        <km-select v-model="categorisePromptCode" height="30px" :placeholder="m.common_promptTemplate()" :options="prompts" :option-show="(el) =&gt; el.category === &quot;rag&quot;" has-dropdown-search />
        <div class="cluster mt-sm">
          <div class="flex-none">
            <km-btn flat simple :label="categorisePromptCode ? m.common_openPromptTemplate() : m.common_openPromptTemplatesLibrary()" icon-size="16px" icon="chat" @click="openPromptTemplate" />
          </div>
        </div>
        <div class="km-field text-secondary-text pb-xs pl-sm mt-md">{{ m.ragTools_questionClassificationTopics() }}</div>
        <km-input-list-add v-model="categories" :btn-label="m.common_add()" />
      </km-section>
    </template>
  </div>
</template>

<script>
import { m } from '@/paraglide/messages'
import { ref, computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'

export default {
  props: ['prompt', 'selectedPrompt'],
  emits: ['cancel', 'remove', 'openTest'],

  setup() {
    const queries = useEntityQueries()
    const { activeVariant, updateVariantField } = useVariantEntityDetail('rag_tools')
    const { data: promptListData } = queries.promptTemplates.useList()
    const promptItems = computed(() => promptListData.value?.items ?? [])
    return {
      m,
      activeVariant,
      updateVariantField,
      promptItems,
      checkForHallucinateMode: ref('logs'),
    }
  },
  computed: {
    categories: {
      get() {
        return this.activeVariant?.post_process?.categorization?.categories || []
      },
      set(value) {
        this.updateVariantField('post_process.categorization.categories', value)
      },
    },
    postProcessEnabled: {
      get() {
        return this.activeVariant?.post_process?.enabled || false
      },
      set(value) {
        this.updateVariantField('post_process.enabled', value)
        if (value && !this.categorisePromptCode) {
          this.categorisePromptCode = {
            system_name: 'DEFAULT_RAG_POST_PROCESSING',
          }
        }
      },
    },
    topics: {
      get() {
        return this.activeVariant?.topics || []
      },
      set(value) {
        this.updateVariantField('topics', value)
      },
    },
    checkIsAnswered: {
      get() {
        return this.activeVariant?.post_process?.answered_check?.enabled || false
      },
      set(value) {
        this.updateVariantField('post_process.answered_check.enabled', value)
      },
    },
    categorisePromptCode: {
      get() {
        return this.prompts.find((el) => el.system_name == this.activeVariant?.post_process?.categorization?.prompt_template)
      },
      set(value) {
        this.updateVariantField('post_process.categorization.prompt_template', value?.system_name)
      },
    },
    categorisePromptId() {
      return this.prompts.find((el) => el.system_name == this.activeVariant?.post_process?.answered_check?.prompt_template)?.value
    },
    detectLanguage: {
      get() {
        return this.activeVariant?.post_process?.detect_question_language?.enabled || false
      },
      set(value) {
        this.updateVariantField('post_process.detect_question_language.enabled', value)
      },
    },
    languageDetectPromptCode: {
      get() {
        return this.prompts.find((el) => el.system_name == this.activeVariant?.post_process?.detect_question_language?.prompt_template)
      },
      set(value) {
        this.updateVariantField('post_process.detect_question_language.prompt_template', value?.system_name)
      },
    },
    languageDetectPromptId() {
      return this.prompts.find((el) => el.system_name == this.activeVariant?.post_process?.detect_question_language?.prompt_template)
        ?.value
    },
    checkIsHallucinate: {
      get() {
        return this.activeVariant?.post_process?.check_is_hallucinate?.enabled || false
      },
      set(value) {
        this.updateVariantField('post_process.check_is_hallucinate.enabled', value)
      },
    },
    hallucinatePromptId() {
      return this.prompts.find((el) => el.system_name == this.activeVariant?.post_process?.check_is_hallucinate?.prompt_template)?.value
    },
    hallucinatePromptCode: {
      get() {
        return this.prompts.find((el) => el.system_name == this.activeVariant?.post_process?.check_is_hallucinate?.prompt_template)
      },
      set(value) {
        this.updateVariantField('post_process.check_is_hallucinate.prompt_template', value?.system_name)
      },
    },

    prompts() {
      return (this.promptItems ?? []).map((item) => ({
        label: item.name,
        value: item.id,
        system_name: item.system_name,
        category: item.category,
      }))
    },
    hasError() {
      return !(this.prompt.name && this.prompt.text && this.prompt.description)
    },
  },
  created() {},
  methods: {
    openPromptTemplate() {
      if (this.categorisePromptCode) {
        this.navigate(`prompt-templates/${this.categorisePromptCode.value}`)
      } else {
        this.navigate('prompt-templates')
      }
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`/${path}`)
      }
    },
  },
}
</script>
