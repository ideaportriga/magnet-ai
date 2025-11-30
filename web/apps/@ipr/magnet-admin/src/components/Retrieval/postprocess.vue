<template lang="pug">
.ba-border.bg-white.border-radius-12.q-pa-lg(style='min-width: 300px')
  km-section(title='Answered / Not answered check', subTitle='Turn on this option for monitoring purposes. Makes one extra call to LLM')
    q-toggle.q-mb-lg(v-model='checkIsAnswered', dense)
    template(v-if='checkIsAnswered')
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Prompt template
      km-select(height='30px', placeholder='Prompt template', :options='prompts', v-model='answeredPromptCode', hasDropdownSearch)
      .row.q-mt-sm
        .col-auto
          km-btn(
            flat,
            simple,
            :label='answeredPromptCode ? "Open Prompt Template" : "Open Prompt Templates Library"',
            iconSize='16px',
            icon='fas fa-comment-dots',
            @click='answeredPromptCode ? navigate(`prompt-templates/${answeredPromptId}`) : navigate("prompt-templates")'
          )

  q-separator.q-my-lg
  km-section(
    title='Check for hallucinations',
    subTitle='Ask LLM to review its own response. A hallucination is a response that is not grounded in provided context'
  )
    q-toggle.q-mb-lg(v-model='checkIsHallucinate', dense)
    template(v-if='checkIsHallucinate')
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Prompt template
      km-select(height='30px', placeholder='Prompt template', :options='prompts', v-model='hallucinatePromptCode', hasDropdownSearch)
      .row.q-mt-sm
        .col-auto
          km-btn(
            flat,
            simple,
            :label='hallucinatePromptCode ? "Open Prompt Template" : "Open Prompt Templates Library"',
            iconSize='16px',
            icon='fas fa-comment-dots',
            @click='hallucinatePromptCode ? navigate(`prompt-templates/${hallucinatePromptId}`) : navigate("prompt-templates")'
          )

      .row.q-mt-lg
        .col-auto
          q-radio(v-model='checkForHallucinateMode', val='logs', dense)
        .col
          .column.q-pl-md
            div Only log results
            .col
              .km-field.text-secondary-text Perform check and log yes or no. Makes one extra call to LLM.
      .row.q-mt-lg
        .col.q-mb-md
          q-chip.km-small-chip(color='primary-light', text-color='primary', label='Upcoming feature')
      .row
        .col-auto
          q-radio(v-model='checkForHallucinateMode', val='logsRegenerate', dense, disable)
        .col
          .column.q-pl-md
            div Log results & re-generate answer
            .col
              .km-field.text-secondary-text Perform check and ask the LLM to re-generate the response. Makes X extra calls to LLM.

  q-separator.q-my-lg
  km-section(title='Detect question language', subTitle='Turn on this option for monitoring purposes. Makes one extra call to LLM')
    q-toggle.q-mb-lg(v-model='detectLanguage', dense)
    template(v-if='detectLanguage')
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Prompt template
      km-select(height='30px', placeholder='Prompt template', :options='prompts', v-model='languageDetectPromptCode', hasDropdownSearch)
      .row.q-mt-sm
        .col-auto
          km-btn(
            flat,
            simple,
            :label='languageDetectPromptCode ? "Open Prompt Template" : "Open Prompt Templates Library"',
            iconSize='16px',
            icon='fas fa-comment-dots',
            @click='languageDetectPromptCode ? navigate(`prompt-templates/${languageDetectPromptId}`) : navigate("prompt-templates")'
          )
</template>

<script>
import { ref } from 'vue'

export default {
  props: ['prompt', 'selectedPrompt'],
  emits: ['setProp', 'save', 'cancel', 'remove', 'openTest'],

  setup() {
    return {
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
        return this.$store.getters.retrievalVariant?.post_process?.answered_check?.enabled || false
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'post_process.answered_check.enabled', value })
      },
    },
    answeredPromptCode: {
      get() {
        return this.prompts.find((el) => el.system_name == this.$store.getters.retrievalVariant?.post_process?.answered_check?.prompt_template)
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'post_process.answered_check.prompt_template', value: value?.system_name })
      },
    },
    answeredPromptId() {
      return this.prompts.find((el) => el.system_name == this.$store.getters.retrievalVariant?.post_process?.answered_check?.prompt_template)?.value
    },
    detectLanguage: {
      get() {
        return this.$store.getters.retrievalVariant?.post_process?.detect_question_language?.enabled || false
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'post_process.detect_question_language.enabled', value })
      },
    },
    languageDetectPromptCode: {
      get() {
        return this.prompts.find(
          (el) => el.system_name == this.$store.getters.retrievalVariant?.post_process?.detect_question_language?.prompt_template
        )
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', {
          path: 'post_process.detect_question_language.prompt_template',
          value: value?.system_name,
        })
      },
    },
    languageDetectPromptId() {
      return this.prompts.find(
        (el) => el.system_name == this.$store.getters.retrievalVariant?.post_process?.detect_question_language?.prompt_template
      )?.value
    },
    checkIsHallucinate: {
      get() {
        return this.$store.getters.retrievalVariant?.post_process?.check_is_hallucinate?.enabled || false
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'post_process.check_is_hallucinate.enabled', value })
      },
    },
    hallucinatePromptId() {
      return this.prompts.find((el) => el.system_name == this.$store.getters.retrievalVariant?.post_process?.check_is_hallucinate?.prompt_template)
        ?.value
    },
    hallucinatePromptCode: {
      get() {
        return this.prompts.find((el) => el.system_name == this.$store.getters.retrievalVariant?.post_process?.check_is_hallucinate?.prompt_template)
      },
      set(value) {
        console.log(value)
        this.$store.dispatch('updateNestedRetrievalProperty', {
          path: 'post_process.check_is_hallucinate.prompt_template',
          value: value?.system_name,
        })
      },
    },

    prompts() {
      return (this.$store.getters.prompts ?? [])
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
