<template lang="pug">
div
  km-section(
    title='Enable post-processing',
    subTitle='Enable to collect data about RAG tool calls for monitoring and analysis purposes. Adds extra calls to LLM.'
  )
    q-toggle(v-model='postProcessEnabled', dense)

  template(v-if='postProcessEnabled') 
    q-separator.q-my-lg
    km-section(
      title='Post-processing Prompt Template',
      subTitle='Select post-processing Prompt Template. Add question topics that the LLM will use to classify user questions'
    )
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Prompt template
      km-select(
        height='30px',
        placeholder='Prompt template',
        :options='prompts',
        v-model='categorisePromptCode',
        :option-show='(el) => el.category === "rag"',
        hasDropdownSearch
      )
      .row.q-mt-sm
        .col-auto
          km-btn(
            flat,
            simple,
            :label='categorisePromptCode ? "Open Prompt Template" : "Open Prompt Templates Library"',
            iconSize='16px',
            icon='fas fa-comment-dots',
            @click='openPromptTemplate'
          )

      .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-md Question classification topics
      km-input-list-add(v-model='categories', btnLabel='Add')

  //- q-separator.q-my-lg
  //- km-section(title="Check for hallucinations", subTitle="Ask LLM to review its own response. A hallucination is a response that is not grounded in provided context")
  //-     q-toggle.q-mb-lg(v-model="checkIsHallucinate" dense)
  //-     template(v-if="checkIsHallucinate")
  //-       .km-field.text-secondary-text.q-pb-xs.q-pl-8 Prompt template
  //-       km-select(
  //-         height="30px"
  //-         placeholder='Prompt template',
  //-         :options='prompts',
  //-         v-model="hallucinatePromptCode",
  //-         hasDropdownSearch
  //-         )
  //-       .row.q-mt-sm
  //-         .col-auto
  //-           km-btn(flat simple :label="hallucinatePromptCode? 'Open Prompt Template':'Open Prompt Templates Library'"  iconSize="16px" icon="fas fa-comment-dots",  @click="hallucinatePromptCode ? navigate(`prompt-templates/${hallucinatePromptId}`) : navigate('prompt-templates')" )

  //-       .row.q-mt-lg
  //-         .col-auto
  //-           q-radio(v-model="checkForHallucinateMode" val="logs" dense)
  //-         .col
  //-           .column.q-pl-md
  //-             div Only log results
  //-             .col 
  //-               .km-field.text-secondary-text Perform check and log yes or no. Makes one extra call to LLM.
  //-       .row.q-mt-lg
  //-         .col.q-mb-md
  //-             q-chip.km-small-chip(
  //-             color="primary-light"
  //-             text-color="primary"
  //-             label="Upcoming feature")
  //-       .row
  //-         .col-auto
  //-           q-radio(v-model="checkForHallucinateMode"  val="logsRegenerate" dense disable)
  //-         .col
  //-           .column.q-pl-md
  //-             div Log results & re-generate answer
  //-             .col 
  //-               .km-field.text-secondary-text Perform check and ask the LLM to re-generate the response. Makes X extra calls to LLM.

  //- q-separator.q-my-lg
  //- km-section(title="Detect question language", subTitle="Turn on this option for monitoring purposes. Makes one extra call to LLM")
  //-     q-toggle.q-mb-lg(v-model="detectLanguage" dense)
  //-     template(v-if="detectLanguage")
  //-       .km-field.text-secondary-text.q-pb-xs.q-pl-8 Prompt template 
  //-       km-select(
  //-         height="30px"
  //-         placeholder='Prompt template',
  //-         :options='prompts',
  //-         v-model="languageDetectPromptCode",
  //-         hasDropdownSearch
  //-       )
  //-       .row.q-mt-sm
  //-         .col-auto
  //-           km-btn(flat simple :label="languageDetectPromptCode? 'Open Prompt Template':'Open Prompt Templates Library'"  iconSize="16px" icon="fas fa-comment-dots", @click="languageDetectPromptCode ? navigate(`prompt-templates/${languageDetectPromptId}`) : navigate('prompt-templates')" )
</template>

<script>
import { ref } from 'vue'

export default {
  props: ['prompt', 'selectedPrompt'],
  emits: ['cancel', 'remove', 'openTest'],

  setup() {
    return {
      checkForHallucinateMode: ref('logs'),
    }
  },
  computed: {
    categories: {
      get() {
        return this.$store.getters.ragVariant?.post_process?.categorization?.categories || []
      },
      set(value) {
        this.$store.dispatch('updateNestedRagProperty', { path: 'post_process.categorization.categories', value })
      },
    },
    postProcessEnabled: {
      get() {
        return this.$store.getters.ragVariant?.post_process?.enabled || false
      },
      set(value) {
        this.$store.dispatch('updateNestedRagProperty', { path: 'post_process.enabled', value })
      },
    },
    topics: {
      get() {
        return this.$store.getters.ragVariant?.topics || []
      },
      set(value) {
        this.$store.dispatch('updateNestedRagProperty', { path: 'topics', value })
      },
    },
    checkIsAnswered: {
      get() {
        return this.$store.getters.ragVariant?.post_process?.answered_check?.enabled || false
      },
      set(value) {
        this.$store.dispatch('updateNestedRagProperty', { path: 'post_process.answered_check.enabled', value })
      },
    },
    categorisePromptCode: {
      get() {
        return this.prompts.find((el) => el.system_name == this.$store.getters.ragVariant?.post_process?.categorization?.prompt_template)
      },
      set(value) {
        this.$store.dispatch('updateNestedRagProperty', { path: 'post_process.categorization.prompt_template', value: value?.system_name })
      },
    },
    categorisePromptId() {
      return this.prompts.find((el) => el.system_name == this.$store.getters.ragVariant?.post_process?.answered_check?.prompt_template)?.value
    },
    detectLanguage: {
      get() {
        return this.$store.getters.ragVariant?.post_process?.detect_question_language?.enabled || false
      },
      set(value) {
        this.$store.dispatch('updateNestedRagProperty', { path: 'post_process.detect_question_language.enabled', value })
      },
    },
    languageDetectPromptCode: {
      get() {
        return this.prompts.find((el) => el.system_name == this.$store.getters.ragVariant?.post_process?.detect_question_language?.prompt_template)
      },
      set(value) {
        this.$store.dispatch('updateNestedRagProperty', { path: 'post_process.detect_question_language.prompt_template', value: value?.system_name })
      },
    },
    languageDetectPromptId() {
      return this.prompts.find((el) => el.system_name == this.$store.getters.ragVariant?.post_process?.detect_question_language?.prompt_template)
        ?.value
    },
    checkIsHallucinate: {
      get() {
        return this.$store.getters.ragVariant?.post_process?.check_is_hallucinate?.enabled || false
      },
      set(value) {
        this.$store.dispatch('updateNestedRagProperty', { path: 'post_process.check_is_hallucinate.enabled', value })
      },
    },
    hallucinatePromptId() {
      return this.prompts.find((el) => el.system_name == this.$store.getters.ragVariant?.post_process?.check_is_hallucinate?.prompt_template)?.value
    },
    hallucinatePromptCode: {
      get() {
        return this.prompts.find((el) => el.system_name == this.$store.getters.ragVariant?.post_process?.check_is_hallucinate?.prompt_template)
      },
      set(value) {
        console.log(value)
        this.$store.dispatch('updateNestedRagProperty', { path: 'post_process.check_is_hallucinate.prompt_template', value: value?.system_name })
      },
    },

    prompts() {
      return (this.$store.getters.prompts ?? []).map((item) => ({
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
      //categorisePromptCode ? navigate(`prompt-templates/${categorisePromptId}`) : navigate('prompt-templates')
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
