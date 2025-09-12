<template lang="pug">
div
  km-section(title='Header configuration', subTitle='Configure heading and subheading for your Retrieval tool')
    .q-mb-lg
      .km-input-label Heading text
      km-input(@input='headingText = $event', :model-value='headingText', placeholder='E.g. Welcome to our Retrieval Tool!')
      .km-tiny Not displayed if left blank
    div
      .km-input-label Subheading text
      km-input(@input='subHeadingText = $event', :model-value='subHeadingText', placeholder='E.g. Use this tool to search our knowledge base')
      .km-tiny Not displayed if left blank
  q-separator.q-my-lg
  km-section(title='User feedback', subTitle='Allow users to send their feedback in form of like or dislike')
    q-toggle.q-mb-lg(v-model='isUserFeedbackOn', dense)
  q-separator.q-my-lg
  km-section(title='Sample questions', subTitle='Display up to 3 question suggestions to help users formulate their questions')
    q-toggle.q-mb-lg(v-model='isSampleQestion', dense)
    template(v-if='isSampleQestion')
      .q-mb-lg
        .km-input-label Question 1
        km-input(v-model='question1', placeholder='What are our most popular pricing plans?')
      .q-mb-lg
        .km-input-label Question 2
        km-input(v-model='question2', placeholder='How to change password in mobile application?')
      div
        .km-input-label Question 3
        km-input(v-model='question3', placeholder='What is the maximum discount that can be applied on top of other discounts?')
</template>

<script>
export default {
  props: [],
  emits: [],

  setup() {
    return {}
  },
  computed: {
    isAllowToBypassCache: {
      get() {
        return this.$store.getters.retrievalVariant?.ui_settings?.offer_to_bypass_cache || false
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'ui_settings.offer_to_bypass_cache', value })
      },
    },
    isUserFeedbackOn: {
      get() {
        return this.$store.getters.retrievalVariant?.ui_settings?.user_fideback || false
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'ui_settings.user_fideback', value })
      },
    },
    headingText: {
      get() {
        return this.$store.getters.retrievalVariant?.ui_settings?.header_configuration?.header || ''
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'ui_settings.header_configuration.header', value })
      },
    },
    subHeadingText: {
      get() {
        return this.$store.getters.retrievalVariant?.ui_settings?.header_configuration?.sub_header || ''
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'ui_settings.header_configuration.sub_header', value })
      },
    },
    isShowLinkTitlesOn: {
      get() {
        return true
      },
    },
    isSampleQestion: {
      get() {
        return this.$store.getters.retrievalVariant?.ui_settings?.sample_questions?.enabled || false
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'ui_settings.sample_questions.enabled', value })
      },
    },
    question1: {
      get() {
        return this.$store.getters.retrievalVariant?.ui_settings?.sample_questions?.questions?.question1
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'ui_settings.sample_questions.questions.question1', value })
      },
    },
    question2: {
      get() {
        return this.$store.getters.retrievalVariant?.ui_settings?.sample_questions?.questions?.question2
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'ui_settings.sample_questions.questions.question2', value })
      },
    },
    question3: {
      get() {
        return this.$store.getters.retrievalVariant?.ui_settings?.sample_questions?.questions?.question3
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'ui_settings.sample_questions.questions.question3', value })
      },
    },
  },
  created() {},
  methods: {},
}
</script>
