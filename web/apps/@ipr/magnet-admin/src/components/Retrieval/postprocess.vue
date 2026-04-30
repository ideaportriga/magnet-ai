<template>
  <div class="ba-border bg-white border-radius-12 p-lg" style="min-inline-size: 300px">
    <km-section :title="m.retrieval_answeredCheck()" :sub-title="m.subtitle_turnOnMonitoring()">
      <km-toggle v-model="checkIsAnswered" class="mb-lg" dense />
      <template v-if="checkIsAnswered">
        <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_promptTemplate() }}</div>
        <km-select v-model="answeredPromptCode" height="30px" :placeholder="m.common_promptTemplate()" :options="prompts" has-dropdown-search />
        <div class="cluster mt-sm">
          <div class="flex-none">
            <km-btn flat simple :label="answeredPromptCode ? m.common_openPromptTemplate() : m.common_openPromptTemplatesLibrary()" icon-size="16px" icon="chat" @click="answeredPromptCode ? navigate(`prompt-templates/${answeredPromptId}`) : navigate(&quot;prompt-templates&quot;)" />
          </div>
        </div>
      </template>
    </km-section>
    <km-separator class="my-lg" />
    <km-section :title="m.retrieval_checkForHallucinations()" :sub-title="m.subtitle_hallucinationCheck()">
      <km-toggle v-model="checkIsHallucinate" class="mb-lg" dense />
      <template v-if="checkIsHallucinate">
        <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_promptTemplate() }}</div>
        <km-select v-model="hallucinatePromptCode" height="30px" :placeholder="m.common_promptTemplate()" :options="prompts" has-dropdown-search />
        <div class="cluster mt-sm">
          <div class="flex-none">
            <km-btn flat simple :label="hallucinatePromptCode ? m.common_openPromptTemplate() : m.common_openPromptTemplatesLibrary()" icon-size="16px" icon="chat" @click="hallucinatePromptCode ? navigate(`prompt-templates/${hallucinatePromptId}`) : navigate(&quot;prompt-templates&quot;)" />
          </div>
        </div>
        <div class="cluster mt-lg">
          <div class="flex-none">
            <km-radio v-model="checkForHallucinateMode" val="logs" dense />
          </div>
          <div class="flex-1">
            <div class="stack pl-md">
              <div>{{ m.retrieval_onlyLogResults() }}</div>
              <div class="full-width">
                <div class="km-field text-secondary-text">{{ m.retrieval_onlyLogResultsDesc() }}</div>
              </div>
            </div>
          </div>
        </div>
        <div class="cluster mt-lg">
          <div class="full-width mb-md">
            <km-chip tone="brand" class="km-small-chip" :label="m.common_upcomingFeature()" />
          </div>
        </div>
        <div class="cluster">
          <div class="flex-none">
            <km-radio v-model="checkForHallucinateMode" val="logsRegenerate" dense disable />
          </div>
          <div class="flex-1">
            <div class="stack pl-md">
              <div>{{ m.retrieval_logAndRegenerate() }}</div>
              <div class="full-width">
                <div class="km-field text-secondary-text">{{ m.retrieval_logAndRegenerateDesc() }}</div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </km-section>
    <km-separator class="my-lg" />
    <km-section :title="m.retrieval_detectQuestionLanguage()" :sub-title="m.subtitle_turnOnMonitoring()">
      <km-toggle v-model="detectLanguage" class="mb-lg" dense />
      <template v-if="detectLanguage">
        <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_promptTemplate() }}</div>
        <km-select v-model="languageDetectPromptCode" height="30px" :placeholder="m.common_promptTemplate()" :options="prompts" has-dropdown-search />
        <div class="cluster mt-sm">
          <div class="flex-none">
            <km-btn flat simple :label="languageDetectPromptCode ? m.common_openPromptTemplate() : m.common_openPromptTemplatesLibrary()" icon-size="16px" icon="chat" @click="languageDetectPromptCode ? navigate(`prompt-templates/${languageDetectPromptId}`) : navigate(&quot;prompt-templates&quot;)" />
          </div>
        </div>
      </template>
    </km-section>
  </div>
</template>

<script>
import { m } from '@/paraglide/messages'
import { ref, computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'

export default {
  props: ['prompt', 'selectedPrompt'],
  emits: ['setProp', 'save', 'cancel', 'remove', 'openTest'],

  setup() {
    const queries = useEntityQueries()
    const { activeVariant, updateVariantField } = useVariantEntityDetail('retrieval')
    const { data: promptListData } = queries.promptTemplates.useList()
    const promptItems = computed(() => promptListData.value?.items ?? [])
    return {
      m,
      activeVariant,
      updateVariantField,
      promptItems,
      test: ref(true),
      iconPicker: ref(false),
      showError: ref(false),
      selectedEntity: ref(),
      promptInput: ref(null),
      llm: ref(true),
      checkForHallucinateMode: ref('logs'),
    }
  },
  computed: {
    checkIsAnswered: {
      get() {
        return this.activeVariant?.post_process?.answered_check?.enabled || false
      },
      set(value) {
        this.updateVariantField('post_process.answered_check.enabled', value)
      },
    },
    answeredPromptCode: {
      get() {
        return this.prompts.find((el) => el.system_name == this.activeVariant?.post_process?.answered_check?.prompt_template)
      },
      set(value) {
        this.updateVariantField('post_process.answered_check.prompt_template', value?.system_name)
      },
    },
    answeredPromptId() {
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
        return this.prompts.find(
          (el) => el.system_name == this.activeVariant?.post_process?.detect_question_language?.prompt_template
        )
      },
      set(value) {
        this.updateVariantField('post_process.detect_question_language.prompt_template', value?.system_name)
      },
    },
    languageDetectPromptId() {
      return this.prompts.find(
        (el) => el.system_name == this.activeVariant?.post_process?.detect_question_language?.prompt_template
      )?.value
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
      return this.prompts.find((el) => el.system_name == this.activeVariant?.post_process?.check_is_hallucinate?.prompt_template)
        ?.value
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
      return (this.promptItems ?? [])
        .map((item) => ({ label: item.name, value: item.id, system_name: item.system_name, category: item?.category }))
        .filter((el) => el.category === 'rag')
    },
    hasError() {
      return !(this.prompt.name && this.prompt.text && this.prompt.description)
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
    addField(control) {
      const pos = this.promptInput?.getCursorIndex() ?? 0
      let text = this.prompt?.text ?? ''
      text = `${text.slice(0, pos).trimEnd()} {{${this.selectedEntity}.${control.name}}} ${text.slice(pos).trimStart()}`
      this.setProp('text', text)
    },
    setCollection(selected) {
      this.publicSelected = selected.map(({ value }) => value)
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`/${path}`)
      }
    },
  },
}
</script>
