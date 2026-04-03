<template lang="pug">
.ba-border.bg-white.border-radius-12.q-pa-lg(style='min-width: 300px')
  km-section(:title='m.retrieval_answeredCheck()', :subTitle='m.subtitle_turnOnMonitoring()')
    q-toggle.q-mb-lg(v-model='checkIsAnswered', dense)
    template(v-if='checkIsAnswered')
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.common_promptTemplate() }}
      km-select(height='30px', :placeholder='m.common_promptTemplate()', :options='prompts', v-model='answeredPromptCode', hasDropdownSearch)
      .row.q-mt-sm
        .col-auto
          km-btn(
            flat,
            simple,
            :label='answeredPromptCode ? m.common_openPromptTemplate() : m.common_openPromptTemplatesLibrary()',
            iconSize='16px',
            icon='fas fa-comment-dots',
            @click='answeredPromptCode ? navigate(`prompt-templates/${answeredPromptId}`) : navigate("prompt-templates")'
          )

  q-separator.q-my-lg
  km-section(
    :title='m.retrieval_checkForHallucinations()',
    :subTitle='m.subtitle_hallucinationCheck()'
  )
    q-toggle.q-mb-lg(v-model='checkIsHallucinate', dense)
    template(v-if='checkIsHallucinate')
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.common_promptTemplate() }}
      km-select(height='30px', :placeholder='m.common_promptTemplate()', :options='prompts', v-model='hallucinatePromptCode', hasDropdownSearch)
      .row.q-mt-sm
        .col-auto
          km-btn(
            flat,
            simple,
            :label='hallucinatePromptCode ? m.common_openPromptTemplate() : m.common_openPromptTemplatesLibrary()',
            iconSize='16px',
            icon='fas fa-comment-dots',
            @click='hallucinatePromptCode ? navigate(`prompt-templates/${hallucinatePromptId}`) : navigate("prompt-templates")'
          )

      .row.q-mt-lg
        .col-auto
          q-radio(v-model='checkForHallucinateMode', val='logs', dense)
        .col
          .column.q-pl-md
            div {{ m.retrieval_onlyLogResults() }}
            .col
              .km-field.text-secondary-text {{ m.retrieval_onlyLogResultsDesc() }}
      .row.q-mt-lg
        .col.q-mb-md
          q-chip.km-small-chip(color='primary-light', text-color='primary', :label='m.common_upcomingFeature()')
      .row
        .col-auto
          q-radio(v-model='checkForHallucinateMode', val='logsRegenerate', dense, disable)
        .col
          .column.q-pl-md
            div {{ m.retrieval_logAndRegenerate() }}
            .col
              .km-field.text-secondary-text {{ m.retrieval_logAndRegenerateDesc() }}

  q-separator.q-my-lg
  km-section(:title='m.retrieval_detectQuestionLanguage()', :subTitle='m.subtitle_turnOnMonitoring()')
    q-toggle.q-mb-lg(v-model='detectLanguage', dense)
    template(v-if='detectLanguage')
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.common_promptTemplate() }}
      km-select(height='30px', :placeholder='m.common_promptTemplate()', :options='prompts', v-model='languageDetectPromptCode', hasDropdownSearch)
      .row.q-mt-sm
        .col-auto
          km-btn(
            flat,
            simple,
            :label='languageDetectPromptCode ? m.common_openPromptTemplate() : m.common_openPromptTemplatesLibrary()',
            iconSize='16px',
            icon='fas fa-comment-dots',
            @click='languageDetectPromptCode ? navigate(`prompt-templates/${languageDetectPromptId}`) : navigate("prompt-templates")'
          )
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
